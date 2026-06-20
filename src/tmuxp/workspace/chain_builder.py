"""Build a tmux workspace through libtmux's experimental chain API.

``ChainWorkspaceBuilder`` is an alternative to
:class:`~tmuxp.workspace.builder.WorkspaceBuilder` that constructs the whole
window/pane tree with one
:class:`~libtmux._experimental.chain.ForwardPlan`, resolved over the minimum
number of tmux invocations instead of one subprocess per ``new-window`` /
``split-window``. Shell commands are delivered either readiness-aware (the
default, matching the classic builder) or batched into the plan.

This is experimental and depends on the pinned ``libtmux._experimental.chain``
worktree; do not ship to a release.
"""

from __future__ import annotations

import typing as t

from libtmux._experimental.chain import ForwardPlan, ServerPlanRunner
from libtmux.pane import Pane
from libtmux.session import Session
from libtmux.window import Window

from tmuxp import exc
from tmuxp.util import run_before_script
from tmuxp.workspace.builder import (
    WorkspaceBuilder,
    _wait_for_pane_ready,
    get_default_columns,
    get_default_rows,
)

if t.TYPE_CHECKING:
    import collections.abc as cabc


Decorate: t.TypeAlias = "cabc.Callable[[t.Any], t.Any]"
SendKeysMode: t.TypeAlias = 't.Literal["readiness", "batched"]'


def _str_or_none(value: t.Any) -> str | None:
    """Narrow an Any config value to a string or None."""
    return value if isinstance(value, str) else None


def _window_start_directory(window_config: dict[str, t.Any]) -> str | None:
    """Resolve a window's start_directory (window, or its first pane)."""
    panes = window_config.get("panes") or [{}]
    return _str_or_none(
        panes[0].get("start_directory", window_config.get("start_directory")),
    )


def _window_shell(window_config: dict[str, t.Any]) -> str | None:
    """Resolve a window's launch command (window_shell, or its first pane shell)."""
    panes = window_config.get("panes") or [{}]
    return _str_or_none(panes[0].get("shell") or window_config.get("window_shell"))


def _pane_start_directory(
    pane_config: dict[str, t.Any], window_config: dict[str, t.Any]
) -> str | None:
    """Resolve a pane's start_directory (pane, then window)."""
    return _str_or_none(
        pane_config.get("start_directory", window_config.get("start_directory")),
    )


def _pane_shell(
    pane_config: dict[str, t.Any], window_config: dict[str, t.Any]
) -> str | None:
    """Resolve a pane's launch command (pane shell, then window_shell)."""
    return _str_or_none(pane_config.get("shell", window_config.get("window_shell")))


def _environment(
    config: dict[str, t.Any], window_config: dict[str, t.Any]
) -> dict[str, str] | None:
    """Resolve environment for a pane/window (own, then window default)."""
    value = config.get("environment", window_config.get("environment"))
    return value if isinstance(value, dict) else None


def _rename(name: str) -> Decorate:
    """Return a decorate that renames a window."""
    return lambda handle: handle.window.rename(name)


def _set_window_option(key: str, value: t.Any) -> Decorate:
    """Return a decorate that sets one window option."""
    return lambda handle: handle.window.set_option(key, str(value))


def _select_layout(layout: str) -> Decorate:
    """Return a decorate that applies a window layout."""
    return lambda handle: handle.window.select_layout(layout)


def _send_keys(command: str, *, enter: bool) -> Decorate:
    """Return a decorate that sends keys into a pane (batched mode)."""
    return lambda handle: handle.cmd.send_keys(command, enter=enter)


class ChainWorkspaceBuilder(WorkspaceBuilder):
    """A :class:`WorkspaceBuilder` that builds the tree via the chain API.

    The session, then every window and pane, is described in one
    :class:`~libtmux._experimental.chain.ForwardPlan` seeded from the live
    session (reusing the session's default window as window 1, so nothing is
    orphaned) and resolved in the fewest tmux invocations. Shell commands are
    delivered per ``send_keys_mode``.
    """

    def __init__(
        self,
        *args: t.Any,
        send_keys_mode: SendKeysMode = "readiness",
        **kwargs: t.Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.send_keys_mode: SendKeysMode = send_keys_mode

    def build(self, session: Session | None = None, append: bool = False) -> None:
        """Build the workspace, constructing the window/pane tree via the chain."""
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
            session_name=self.session_config["session_name"], **kwargs
        )
        assert session is not None
        self._session = session
        self.server = session.server
        return session

    def _chain_setup_session(self, session: Session) -> None:
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
        plan: ForwardPlan,
        seed: t.Any,
        window_config: dict[str, t.Any],
        *,
        first_window: bool,
    ) -> None:
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
        enter = pane_config.get("enter", True)
        for command in pane_config.get("shell_command", []):
            handle.do(_send_keys(command["cmd"], enter=command.get("enter", enter)))

    # -- recover objects + deliver commands + focus ------------------------
    def _finalize(
        self, session: Session, windows: list[dict[str, t.Any]], *, append: bool
    ) -> None:
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
                window.panes, window_config["panes"], strict=False
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
