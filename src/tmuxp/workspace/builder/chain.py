"""Build a tmux workspace through libtmux's experimental chain API.

:class:`ChainWorkspaceBuilder` is an experimental alternative to
:class:`~tmuxp.workspace.builder.classic.ClassicWorkspaceBuilder` that describes
the whole window/pane tree in one
:class:`~libtmux._experimental.chain.ForwardPlan` and resolves it in the fewest
tmux invocations, instead of one subprocess per ``new-window`` /
``split-window``. Shell commands are delivered either readiness-aware (the
default, matching the classic builder) or batched into the plan.

The chain API (libtmux#685) is **unreleased**: it is absent from published
libtmux builds. This module imports cleanly without it -- the experimental
import is guarded and :data:`_HAVE_CHAIN` records whether the API is present.
When it is absent, :meth:`ChainWorkspaceBuilder.build` raises
:exc:`~tmuxp.exc.WorkspaceBuilderImportError` so selecting ``workspace_builder:
chain`` fails with an actionable message rather than an import crash.
"""

from __future__ import annotations

import typing as t

from libtmux.pane import Pane
from libtmux.session import Session
from libtmux.window import Window

from tmuxp import exc
from tmuxp.util import run_before_script
from tmuxp.workspace.builder.classic import (
    ClassicWorkspaceBuilder,
    _wait_for_pane_ready,
    get_default_columns,
    get_default_rows,
)

if t.TYPE_CHECKING:
    # The chain API is unreleased (libtmux#685); model the symbols as ``Any``
    # and the feature as absent so this module type-checks on released libtmux.
    ForwardPlan = t.Any
    ServerPlanRunner = t.Any
    _HAVE_CHAIN = False
else:
    try:
        from libtmux._experimental.chain import ForwardPlan, ServerPlanRunner

        _HAVE_CHAIN = True
    except ImportError:
        ForwardPlan = None
        ServerPlanRunner = None
        _HAVE_CHAIN = False


Decorate: t.TypeAlias = t.Callable[[t.Any], t.Any]
SendKeysMode: t.TypeAlias = t.Literal["readiness", "batched"]

_CHAIN_UNAVAILABLE = (
    "ChainWorkspaceBuilder requires the libtmux experimental chain API "
    "(libtmux#685), not available in this libtmux build"
)


def _str_or_none(value: t.Any) -> str | None:
    """Narrow an ``Any`` config value to a ``str`` or ``None``.

    Examples
    --------
    >>> _str_or_none("~/project")
    '~/project'
    >>> _str_or_none(None) is None
    True
    >>> _str_or_none(123) is None
    True
    """
    return value if isinstance(value, str) else None


def _window_start_directory(window_config: dict[str, t.Any]) -> str | None:
    """Resolve a window's start_directory (window, or its first pane).

    Examples
    --------
    >>> _window_start_directory({"start_directory": "/tmp"})
    '/tmp'
    >>> _window_start_directory({"panes": [{"start_directory": "/srv"}]})
    '/srv'
    >>> _window_start_directory({}) is None
    True
    """
    panes = window_config.get("panes") or [{}]
    return _str_or_none(
        panes[0].get("start_directory", window_config.get("start_directory")),
    )


def _window_shell(window_config: dict[str, t.Any]) -> str | None:
    """Resolve a window's launch command (window_shell, or first pane shell).

    Examples
    --------
    >>> _window_shell({"window_shell": "htop"})
    'htop'
    >>> _window_shell({"panes": [{"shell": "top"}]})
    'top'
    >>> _window_shell({}) is None
    True
    """
    panes = window_config.get("panes") or [{}]
    return _str_or_none(panes[0].get("shell") or window_config.get("window_shell"))


def _pane_start_directory(
    pane_config: dict[str, t.Any],
    window_config: dict[str, t.Any],
) -> str | None:
    """Resolve a pane's start_directory (pane, then window).

    Examples
    --------
    >>> _pane_start_directory({"start_directory": "/a"}, {})
    '/a'
    >>> _pane_start_directory({}, {"start_directory": "/b"})
    '/b'
    >>> _pane_start_directory({}, {}) is None
    True
    """
    return _str_or_none(
        pane_config.get("start_directory", window_config.get("start_directory")),
    )


def _pane_shell(
    pane_config: dict[str, t.Any],
    window_config: dict[str, t.Any],
) -> str | None:
    """Resolve a pane's launch command (pane shell, then window_shell).

    Examples
    --------
    >>> _pane_shell({"shell": "fish"}, {})
    'fish'
    >>> _pane_shell({}, {"window_shell": "zsh"})
    'zsh'
    >>> _pane_shell({}, {}) is None
    True
    """
    return _str_or_none(pane_config.get("shell", window_config.get("window_shell")))


def _environment(
    config: dict[str, t.Any],
    window_config: dict[str, t.Any],
) -> dict[str, str] | None:
    """Resolve environment for a pane/window (own, then window default).

    Examples
    --------
    >>> _environment({"environment": {"A": "1"}}, {})
    {'A': '1'}
    >>> _environment({}, {"environment": {"B": "2"}})
    {'B': '2'}
    >>> _environment({}, {}) is None
    True
    """
    value = config.get("environment", window_config.get("environment"))
    return value if isinstance(value, dict) else None


def _rename(name: str) -> Decorate:
    """Return a decorate that renames a window.

    Examples
    --------
    >>> class _Window:
    ...     def rename(self, name):
    ...         return ("rename", name)
    >>> class _Handle:
    ...     window = _Window()
    >>> _rename("editor")(_Handle())
    ('rename', 'editor')
    """
    return lambda handle: handle.window.rename(name)


def _set_window_option(key: str, value: t.Any) -> Decorate:
    """Return a decorate that sets one window option.

    Examples
    --------
    >>> class _Window:
    ...     def set_option(self, key, value):
    ...         return (key, value)
    >>> class _Handle:
    ...     window = _Window()
    >>> _set_window_option("automatic-rename", False)(_Handle())
    ('automatic-rename', 'False')
    """
    return lambda handle: handle.window.set_option(key, str(value))


def _select_layout(layout: str) -> Decorate:
    """Return a decorate that applies a window layout.

    Examples
    --------
    >>> class _Window:
    ...     def select_layout(self, layout):
    ...         return layout
    >>> class _Handle:
    ...     window = _Window()
    >>> _select_layout("main-vertical")(_Handle())
    'main-vertical'
    """
    return lambda handle: handle.window.select_layout(layout)


def _send_keys(command: str, *, enter: bool) -> Decorate:
    """Return a decorate that sends keys into a pane (batched mode).

    Examples
    --------
    >>> class _Cmd:
    ...     def send_keys(self, command, enter):
    ...         return (command, enter)
    >>> class _Handle:
    ...     cmd = _Cmd()
    >>> _send_keys("echo hi", enter=True)(_Handle())
    ('echo hi', True)
    """
    return lambda handle: handle.cmd.send_keys(command, enter=enter)


class ChainWorkspaceBuilder(ClassicWorkspaceBuilder):
    """A :class:`ClassicWorkspaceBuilder` that builds the tree via the chain API.

    The session, then every window and pane, is described in one
    :class:`~libtmux._experimental.chain.ForwardPlan` seeded from the live
    session (reusing the session's default window as window 1, so nothing is
    orphaned) and resolved in the fewest tmux invocations. Shell commands are
    delivered per ``send_keys_mode``.

    This builder is experimental and depends on the unreleased
    ``libtmux._experimental.chain`` API (libtmux#685). Until that ships,
    :meth:`build` raises :exc:`~tmuxp.exc.WorkspaceBuilderImportError`.

    Examples
    --------
    The class imports and subclasses the classic builder even when the chain
    API is absent, so ``workspace_builder: chain`` resolves cleanly:

    >>> from tmuxp.workspace.builder.chain import ChainWorkspaceBuilder
    >>> from tmuxp.workspace.builder.classic import ClassicWorkspaceBuilder
    >>> issubclass(ChainWorkspaceBuilder, ClassicWorkspaceBuilder)
    True
    """

    send_keys_mode: SendKeysMode

    def __init__(
        self,
        *args: t.Any,
        send_keys_mode: SendKeysMode = "readiness",
        **kwargs: t.Any,
    ) -> None:
        """Initialize the chain builder.

        Parameters
        ----------
        *args, **kwargs
            forwarded to
            :class:`~tmuxp.workspace.builder.classic.ClassicWorkspaceBuilder`
            (``session_config``, ``server``, ``plugins``, and the ``on_*``
            callbacks).
        send_keys_mode : {"readiness", "batched"}
            ``"readiness"`` (default) delivers each pane's shell commands after
            the plan resolves, waiting for the prompt like the classic builder;
            ``"batched"`` folds ``send_keys`` into the plan itself.
        """
        super().__init__(*args, **kwargs)
        self.send_keys_mode = send_keys_mode

    def build(self, session: Session | None = None, append: bool = False) -> None:
        """Build the workspace, constructing the window/pane tree via the chain.

        Parameters
        ----------
        session : :class:`libtmux.Session`, optional
            session to build the workspace in; created from ``self.server`` when
            omitted
        append : bool
            append windows to an existing active session

        Raises
        ------
        tmuxp.exc.WorkspaceBuilderImportError
            when the unreleased ``libtmux._experimental.chain`` API
            (libtmux#685) is not importable in the current libtmux build
        """
        if not _HAVE_CHAIN:
            target = "chain"
            raise exc.WorkspaceBuilderImportError(target, reason=_CHAIN_UNAVAILABLE)

        session = self._chain_create_session(session)
        self._chain_setup_session(session)

        windows = self.session_config["windows"]
        plan = ForwardPlan.from_session(session)
        seed = plan.seed
        for index, window_config in enumerate(windows):
            first_window = index == 0 and not append
            self._plan_window(plan, seed, window_config, first_window=first_window)

        plan.run_resolving(ServerPlanRunner(self.server))
        self._finalize(session, windows, append=append)

    # -- session creation + setup ------------------------------------------
    def _chain_create_session(self, session: Session | None) -> Session:
        """Return the session to build in, creating one when not provided."""
        if session is not None:
            self._session = session
            return session
        if not self.server:
            msg = "ChainWorkspaceBuilder.build requires a server or a session"
            raise exc.TmuxpException(msg)

        kwargs: dict[str, t.Any] = {
            "x": get_default_columns(),
            "y": get_default_rows(),
        }
        if "start_directory" in self.session_config:
            kwargs["start_directory"] = self.session_config["start_directory"]
        session = self.server.new_session(
            session_name=self.session_config["session_name"],
            **kwargs,
        )
        assert session is not None
        self._session = session
        self.server = session.server
        return session

    def _chain_setup_session(self, session: Session) -> None:
        """Run plugin/before_script hooks and apply session-level options."""
        for plugin in self.plugins:
            plugin.before_workspace_builder(session)

        if "before_script" in self.session_config:
            cwd = self.session_config.get("start_directory")
            try:
                run_before_script(
                    self.session_config["before_script"],
                    cwd=cwd,
                    on_line=self.on_script_output,
                )
            except Exception:
                session.kill()
                raise

        for option, value in self.session_config.get("options", {}).items():
            session.set_option(option, value)
        for option, value in self.session_config.get("global_options", {}).items():
            session.set_option(option, value, global_=True)
        for key, value in self.session_config.get("environment", {}).items():
            session.set_environment(key, value)

    # -- plan the window/pane tree -----------------------------------------
    def _plan_window(
        self,
        plan: t.Any,
        seed: t.Any,
        window_config: dict[str, t.Any],
        *,
        first_window: bool,
    ) -> None:
        """Describe one window and its panes on the forward plan."""
        name = window_config.get("window_name")
        if first_window:
            window = seed.initial_window
            first_pane = seed.initial_pane
            if name:
                window.do(_rename(name))
        else:
            window = seed.new_window(
                name=name,
                start_directory=_window_start_directory(window_config),
                environment=_environment(window_config, window_config),
                window_shell=_window_shell(window_config),
            )
            first_pane = window

        for key, value in window_config.get("options", {}).items():
            window.do(_set_window_option(key, value))

        panes = window_config["panes"]
        pane_handles = [first_pane]
        previous = first_pane
        for pane_config in panes[1:]:
            handle = previous.split(
                start_directory=_pane_start_directory(pane_config, window_config),
                shell=_pane_shell(pane_config, window_config),
                environment=_environment(pane_config, window_config),
            )
            pane_handles.append(handle)
            previous = handle

        if "layout" in window_config:
            window.do(_select_layout(window_config["layout"]))

        if self.send_keys_mode == "batched":
            for handle, pane_config in zip(pane_handles, panes, strict=False):
                self._plan_pane_keys(handle, pane_config)

    def _plan_pane_keys(self, handle: t.Any, pane_config: dict[str, t.Any]) -> None:
        """Fold a pane's shell commands into the plan (batched mode)."""
        enter = pane_config.get("enter", True)
        for command in pane_config.get("shell_command", []):
            handle.do(_send_keys(command["cmd"], enter=command.get("enter", enter)))

    # -- recover objects + deliver commands + focus ------------------------
    def _finalize(
        self,
        session: Session,
        windows: list[dict[str, t.Any]],
        *,
        append: bool,
    ) -> None:
        """Recover libtmux objects, run hooks, deliver commands, apply focus."""
        session.refresh()
        # Windows in index order == config creation order (default window first,
        # new windows appended); same for a window's panes.
        built = (
            list(session.windows)[-len(windows) :] if append else list(session.windows)
        )

        focus_window: Window | None = None
        for window, window_config in zip(built, windows, strict=False):
            window.refresh()
            for plugin in self.plugins:
                plugin.on_window_create(window)

            focus_pane: Pane | None = None
            for pane, pane_config in zip(
                window.panes,
                window_config["panes"],
                strict=False,
            ):
                if self.send_keys_mode == "readiness":
                    self._send_pane_commands(pane, pane_config, window_config)
                if pane_config.get("focus"):
                    focus_pane = pane

            self.config_after_window(window, window_config)
            for plugin in self.plugins:
                plugin.after_window_finished(window)
            if focus_pane is not None:
                focus_pane.select()
            if window_config.get("focus"):
                focus_window = window

        if focus_window is not None:
            focus_window.select()

    def _send_pane_commands(
        self,
        pane: Pane,
        pane_config: dict[str, t.Any],
        window_config: dict[str, t.Any],
    ) -> None:
        """Deliver a pane's shell commands readiness-aware (classic semantics)."""
        if _pane_shell(pane_config, window_config) is None:
            _wait_for_pane_ready(pane)

        if "suppress_history" in pane_config:
            suppress = pane_config["suppress_history"]
        else:
            suppress = window_config.get("suppress_history", True)

        enter = pane_config.get("enter", True)
        for command in pane_config.get("shell_command", []):
            pane.send_keys(
                command["cmd"],
                suppress_history=command.get("suppress_history", suppress),
                enter=command.get("enter", enter),
            )
