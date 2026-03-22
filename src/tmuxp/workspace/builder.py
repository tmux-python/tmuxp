"""Create a tmux workspace from a workspace :py:obj:`dict`."""

from __future__ import annotations

import logging
import os
import shlex
import shutil
import time
import typing as t

from libtmux._internal.query_list import ObjectDoesNotExist
from libtmux.pane import Pane
from libtmux.server import Server
from libtmux.session import Session
from libtmux.window import Window

from tmuxp import exc
from tmuxp.log import TmuxpLoggerAdapter
from tmuxp.util import get_current_pane, run_before_script

if t.TYPE_CHECKING:
    from collections.abc import Iterator

logger = logging.getLogger(__name__)


def _wait_for_pane_ready(
    pane: Pane,
    timeout: float = 2.0,
    interval: float = 0.05,
) -> bool:
    """Wait for pane shell to draw its prompt.

    Polls the pane's cursor position until it moves from origin (0, 0),
    indicating the shell has finished initializing and drawn its prompt.

    Parameters
    ----------
    pane : :class:`libtmux.Pane`
        pane to wait for
    timeout : float
        maximum seconds to wait before giving up
    interval : float
        seconds between polling attempts

    Returns
    -------
    bool
        True if pane became ready, False on timeout or error

    Examples
    --------
    >>> pane = session.active_window.active_pane

    Wait for the shell to be ready:

    >>> _wait_for_pane_ready(pane, timeout=5.0)
    True
    """
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        try:
            pane.refresh()
        except Exception:
            logger.debug(
                "pane refresh failed during readiness check",
                exc_info=True,
                extra={"tmux_pane": str(pane.pane_id)},
            )
            return False
        if pane.cursor_x != "0" or pane.cursor_y != "0":
            logger.debug(
                "pane ready, cursor moved from origin",
                extra={"tmux_pane": str(pane.pane_id)},
            )
            return True
        time.sleep(interval)
    logger.debug(
        "pane readiness check timed out after %.1f seconds",
        timeout,
        extra={"tmux_pane": str(pane.pane_id)},
    )
    return False


COLUMNS_FALLBACK = 80


def get_default_columns() -> int:
    """Return default session column size use when building new tmux sessions."""
    return int(
        os.getenv("TMUXP_DEFAULT_COLUMNS", os.getenv("COLUMNS", COLUMNS_FALLBACK)),
    )


ROWS_FALLBACK = int(os.getenv("TMUXP_DEFAULT_ROWS", os.getenv("ROWS", 24)))


def get_default_rows() -> int:
    """Return default session row size use when building new tmux sessions."""
    return int(os.getenv("TMUXP_DEFAULT_ROWS", os.getenv("ROWS", ROWS_FALLBACK)))


class WorkspaceBuilder:
    """Load workspace from workspace :py:obj:`dict` object.

    Build tmux workspace from a configuration. Creates and names windows, sets options,
    splits windows into panes.

    Examples
    --------
    >>> import yaml

    >>> session_config = yaml.load('''
    ...     session_name: sample workspace
    ...     start_directory: '~'
    ...     windows:
    ...     - window_name: editor
    ...       layout: main-vertical
    ...       panes:
    ...       - shell_command:
    ...         - cmd: vim
    ...       - shell_command:
    ...         - cmd: echo "hey"
    ...
    ...     - window_name: logging
    ...       panes:
    ...       - shell_command:
    ...         - cmd: tail | echo 'hi'
    ...
    ...     - window_name: test
    ...       panes:
    ...       - shell_command:
    ...         - cmd: htop
    ... ''', Loader=yaml.Loader)

    >>> builder = WorkspaceBuilder(session_config=session_config, server=server)

    **New session:**

    >>> builder.build()

    >>> new_session = builder.session

    >>> new_session.name == 'sample workspace'
    True

    >>> len(new_session.windows)
    3

    >>> sorted([window.name for window in new_session.windows])
    ['editor', 'logging', 'test']

    **Existing session:**

    >>> len(session.windows)
    1

    >>> builder.build(session=session)

    _Caveat:_ Preserves old session name:

    >>> session.name == 'sample workspace'
    False

    >>> len(session.windows)
    3

    >>> sorted([window.name for window in session.windows])
    ['editor', 'logging', 'test']

    **Progress callback:**

    >>> calls: list[str] = []
    >>> progress_cfg = {
    ...     "session_name": "progress-demo",
    ...     "windows": [{"window_name": "main", "panes": [{"shell_command": []}]}],
    ... }
    >>> builder = WorkspaceBuilder(
    ...     session_config=progress_cfg,
    ...     server=server,
    ...     on_progress=calls.append,
    ... )
    >>> builder.build()
    >>> "Workspace built" in calls
    True

    **Before-script hook:**

    >>> hook_calls: list[bool] = []
    >>> no_script_cfg = {
    ...     "session_name": "hook-demo",
    ...     "windows": [{"window_name": "main", "panes": [{"shell_command": []}]}],
    ... }
    >>> builder = WorkspaceBuilder(
    ...     session_config=no_script_cfg,
    ...     server=server,
    ...     on_before_script=lambda: hook_calls.append(True),
    ... )
    >>> builder.build()
    >>> hook_calls  # no before_script in config, callback not fired
    []

    **Script output hook:**

    >>> script_lines: list[str] = []
    >>> no_script_cfg2 = {
    ...     "session_name": "script-output-demo",
    ...     "windows": [{"window_name": "main", "panes": [{"shell_command": []}]}],
    ... }
    >>> builder = WorkspaceBuilder(
    ...     session_config=no_script_cfg2,
    ...     server=server,
    ...     on_script_output=script_lines.append,
    ... )
    >>> builder.build()
    >>> script_lines  # no before_script in config, callback not fired
    []

    **Build events hook:**

    >>> events: list[dict] = []
    >>> event_cfg = {
    ...     "session_name": "events-demo",
    ...     "windows": [{"window_name": "main", "panes": [{"shell_command": []}]}],
    ... }
    >>> builder = WorkspaceBuilder(
    ...     session_config=event_cfg,
    ...     server=server,
    ...     on_build_event=events.append,
    ... )
    >>> builder.build()
    >>> [e["event"] for e in events]
    ['session_created', 'window_started', 'pane_creating',
     'window_done', 'workspace_built']
    >>> next(e for e in events if e["event"] == "session_created")["session_pane_total"]
    1

    **Build events with before_script:**

    ``before_script_started`` fires before the script runs;
    ``before_script_done`` fires in ``finally`` (success or failure).

    >>> script_events: list[dict] = []
    >>> script_event_cfg = {
    ...     "session_name": "script-events-demo",
    ...     "before_script": "echo hello",
    ...     "windows": [{"window_name": "main", "panes": [{"shell_command": []}]}],
    ... }
    >>> builder = WorkspaceBuilder(
    ...     session_config=script_event_cfg,
    ...     server=server,
    ...     on_build_event=script_events.append,
    ... )
    >>> builder.build()
    >>> event_names = [e["event"] for e in script_events]
    >>> "before_script_started" in event_names
    True
    >>> "before_script_done" in event_names
    True
    >>> bs_start = event_names.index("before_script_started")
    >>> bs_done = event_names.index("before_script_done")
    >>> win_start = event_names.index("window_started")
    >>> bs_start < bs_done < win_start
    True

    The normal phase of loading is:

    1. Load JSON / YAML file via :class:`pathlib.Path`::

           from tmuxp._internal import config_reader
           session_config = config_reader.ConfigReader._load(raw_yaml)

       The reader automatically detects the file type from :attr:`pathlib.suffix`.

       We can also parse raw file::

           import pathlib
           from tmuxp._internal import config_reader

           session_config = config_reader.ConfigReader._from_file(
               pathlib.Path('path/to/config.yaml')
           )

    2. :meth:`config.expand` session_config inline shorthand::

           from tmuxp import config
           session_config = config.expand(session_config)

    3. :meth:`config.trickle` passes down default values from session
       -> window -> pane if applicable::

           session_config = config.trickle(session_config)

    4. (You are here) We will create a :class:`libtmux.Session` (a real
       ``tmux(1)`` session) and iterate through the list of windows, and
       their panes, returning full :class:`libtmux.Window` and
       :class:`libtmux.Pane` objects each step of the way::

           workspace = WorkspaceBuilder(session_config=session_config, server=server)

    It handles the magic of cases where the user may want to start
    a session inside tmux (when `$TMUX` is in the env variables).
    """

    server: Server
    _session: Session | None
    session_name: str
    on_progress: t.Callable[[str], None] | None
    on_before_script: t.Callable[[], None] | None
    on_script_output: t.Callable[[str], None] | None
    on_build_event: t.Callable[[dict[str, t.Any]], None] | None

    def __init__(
        self,
        session_config: dict[str, t.Any],
        server: Server,
        plugins: list[t.Any] | None = None,
        on_progress: t.Callable[[str], None] | None = None,
        on_before_script: t.Callable[[], None] | None = None,
        on_script_output: t.Callable[[str], None] | None = None,
        on_build_event: t.Callable[[dict[str, t.Any]], None] | None = None,
    ) -> None:
        """Initialize workspace loading.

        Parameters
        ----------
        session_config : dict
            session config, includes a :py:obj:`list` of ``windows``.

        plugins : list
            plugins to be used for this session

        server : :class:`libtmux.Server`
            tmux server to build session in

        on_progress : callable, optional
            callback for progress updates during building

        on_before_script : callable, optional
            called just before ``before_script`` runs; use to clear the terminal
            (e.g. stop a spinner) so script output is not interleaved

        on_script_output : callable, optional
            called with each output line from ``before_script`` subprocess; when
            set, raw TTY tee is suppressed so the caller can route lines to a
            live panel instead

        on_build_event : callable, optional
            called with a dict event at each structural build milestone (session
            created, window started/done, pane creating, workspace built); used
            by the CLI to render a live session tree

        Notes
        -----
        TODO: Initialize :class:`libtmux.Session` from here, in
        ``self.session``.
        """
        if plugins is None:
            plugins = []
        if not session_config:
            raise exc.EmptyWorkspaceException

        # validation.validate_schema(session_config)

        assert isinstance(server, Server)
        self.server = server

        self.session_config = session_config
        self.plugins = plugins
        self.on_progress = on_progress
        self.on_before_script = on_before_script
        self.on_script_output = on_script_output
        self.on_build_event = on_build_event

        if self.server is not None and self.session_exists(
            session_name=self.session_config["session_name"],
        ):
            try:
                session = self.server.sessions.get(
                    session_name=self.session_config["session_name"],
                )
                assert session is not None
                self._session = session
            except ObjectDoesNotExist:
                pass

    @property
    def session(self) -> Session:
        """Return tmux session using in workspace builder session."""
        if self._session is None:
            raise exc.SessionMissingWorkspaceException
        return self._session

    def session_exists(self, session_name: str) -> bool:
        """Return true if tmux session already exists."""
        assert session_name is not None
        assert isinstance(session_name, str)
        assert self.server is not None
        exists = self.server.has_session(session_name)
        if not exists:
            return exists

        try:
            self.server.sessions.get(session_name=session_name)
        except ObjectDoesNotExist:
            return False
        return True

    def build(
        self,
        session: Session | None = None,
        append: bool = False,
        here: bool = False,
    ) -> None:
        """Build tmux workspace in session.

        Optionally accepts ``session`` to build with only session object.

        Without ``session``, it will use :class:`libmtux.Server` at ``self.server``
        passed in on initialization to create a new Session object.

        Parameters
        ----------
        session : :class:`libtmux.Session`
            session to build workspace in
        append : bool
            append windows in current active session
        here : bool
            reuse current window for first window and rename session
        """
        if not session:
            if not self.server:
                msg = (
                    "WorkspaceBuilder.build requires server to be passed "
                    "on initialization, or pass in session object to here."
                )
                raise exc.TmuxpException(
                    msg,
                )
            new_session_kwargs = {}
            if "start_directory" in self.session_config:
                new_session_kwargs["start_directory"] = self.session_config[
                    "start_directory"
                ]

            if os.getenv("TMUXP_DETECT_TERMINAL_SIZE", "1") == "1":
                terminal_size = shutil.get_terminal_size(
                    fallback=(get_default_columns(), get_default_rows()),
                )
                new_session_kwargs["x"] = terminal_size.columns
                new_session_kwargs["y"] = terminal_size.lines

            session = self.server.new_session(
                session_name=self.session_config["session_name"],
                **new_session_kwargs,
            )
            assert session is not None

            assert self.session_config["session_name"] == session.name
            assert len(self.session_config["session_name"]) > 0

        assert session is not None
        assert session.name is not None

        if self.on_progress:
            self.on_progress(f"Session created: {session.name}")

        self._session = session
        if self.on_build_event:
            self.on_build_event(
                {
                    "event": "session_created",
                    "name": session.name,
                    "window_total": len(self.session_config["windows"]),
                    "session_pane_total": sum(
                        len(w.get("panes", [])) for w in self.session_config["windows"]
                    ),
                }
            )
        _log = TmuxpLoggerAdapter(
            logger,
            {"tmux_session": self.session_config["session_name"]},
        )
        _log.info("session created")

        assert session.server is not None

        self.server: Server = session.server
        assert self.server.sessions is not None
        assert self.server.has_session(session.name)
        assert session.id

        assert isinstance(session, Session)

        for plugin in self.plugins:
            plugin.before_workspace_builder(self.session)

        focus = None

        if "before_script" in self.session_config:
            if self.on_before_script:
                self.on_before_script()
            if self.on_build_event:
                self.on_build_event({"event": "before_script_started"})
            try:
                cwd = None

                # we want to run the before_script file cwd'd from the
                # session start directory, if it exists.
                if "start_directory" in self.session_config:
                    cwd = self.session_config["start_directory"]
                _log.debug(
                    "running before script",
                )
                run_before_script(
                    self.session_config["before_script"],
                    cwd=cwd,
                    on_line=self.on_script_output,
                )
            except Exception:
                _log.error(
                    "before script failed",
                    extra={
                        "tmux_config_path": str(
                            self.session_config["before_script"],
                        ),
                    },
                )
                self.session.kill()
                raise
            finally:
                if self.on_build_event:
                    self.on_build_event({"event": "before_script_done"})

        if "options" in self.session_config:
            for option, value in self.session_config["options"].items():
                self.session.set_option(option, value)

        if "global_options" in self.session_config:
            for option, value in self.session_config["global_options"].items():
                self.session.set_option(option, value, global_=True)

        if "environment" in self.session_config:
            for option, value in self.session_config["environment"].items():
                self.session.set_environment(option, value)

        # Set lifecycle tmux hooks
        if "on_project_exit" in self.session_config:
            exit_cmds = self.session_config["on_project_exit"]
            if isinstance(exit_cmds, str):
                exit_cmds = [exit_cmds]
            _joined = "; ".join(exit_cmds)
            _escaped = _joined.replace("'", "'\\''")
            self.session.set_hook("client-detached", f"run-shell '{_escaped}'")

        # Store on_project_stop in session environment for tmuxp stop
        if "on_project_stop" in self.session_config:
            stop_cmds = self.session_config["on_project_stop"]
            if isinstance(stop_cmds, str):
                stop_cmds = [stop_cmds]
            self.session.set_environment(
                "TMUXP_ON_PROJECT_STOP",
                "; ".join(stop_cmds),
            )

        # Store start_directory in session environment for hook cwd
        if "start_directory" in self.session_config:
            self.session.set_environment(
                "TMUXP_START_DIRECTORY",
                self.session_config["start_directory"],
            )

        if here:
            session_name = self.session_config["session_name"]
            if session.name != session_name:
                existing = self.server.sessions.get(
                    session_name=session_name, default=None
                )
                if existing is not None:
                    msg = f"cannot rename to {session_name!r}: session already exists"
                    raise exc.TmuxpException(msg)
                session.rename_session(session_name)

        for window, window_config in self.iter_create_windows(
            session, append, here=here
        ):
            assert isinstance(window, Window)

            for plugin in self.plugins:
                plugin.on_window_create(window)

            focus_pane = None
            for pane, pane_config in self.iter_create_panes(window, window_config):
                assert isinstance(pane, Pane)
                pane = pane

                if pane_config.get("focus"):
                    focus_pane = pane

            if window_config.get("focus"):
                focus = window

            self.config_after_window(window, window_config)

            for plugin in self.plugins:
                plugin.after_window_finished(window)

            if focus_pane:
                focus_pane.select()

            if self.on_build_event:
                self.on_build_event({"event": "window_done"})

        if focus:
            focus.select()

        if self.on_progress:
            self.on_progress("Workspace built")
        _log.info("workspace built")
        if self.on_build_event:
            self.on_build_event({"event": "workspace_built"})

    def iter_create_windows(
        self,
        session: Session,
        append: bool = False,
        here: bool = False,
    ) -> Iterator[t.Any]:
        """Return :class:`libtmux.Window` iterating through session config dict.

        Generator yielding :class:`libtmux.Window` by iterating through
        ``session_config['windows']``.

        Applies ``window_options`` to window.

        Parameters
        ----------
        session : :class:`libtmux.Session`
            session to create windows in
        append : bool
            append windows in current active session
        here : bool
            reuse current window for first window

        Returns
        -------
        tuple of (:class:`libtmux.Window`, ``window_config``)
            Newly created window, and the section from the tmuxp configuration
            that was used to create the window.
        """
        for window_iterator, window_config in enumerate(
            self.session_config["windows"],
            start=1,
        ):
            window_name = window_config.get("window_name", None)

            if self.on_progress:
                self.on_progress(f"Creating window: {window_name or window_iterator}")
            if self.on_build_event:
                self.on_build_event(
                    {
                        "event": "window_started",
                        "name": window_name or str(window_iterator),
                        "pane_total": len(window_config["panes"]),
                    }
                )

            if here and window_iterator == 1:
                # --here: reuse current window for first window
                window = session.active_window
                if window_name:
                    window.rename_window(window_name)

                # Remove extra panes so iter_create_panes starts clean
                _active_pane = window.active_pane
                for _p in list(window.panes):
                    if _p != _active_pane:
                        _p.kill()

                start_directory = window_config.get("start_directory", None)
                panes = window_config["panes"]
                if panes and "start_directory" in panes[0]:
                    start_directory = panes[0]["start_directory"]

                if start_directory:
                    active_pane = window.active_pane
                    if active_pane is not None:
                        active_pane.send_keys(
                            f"cd {shlex.quote(start_directory)}",
                            enter=True,
                        )
            else:
                is_first_window_pass = self.first_window_pass(
                    window_iterator,
                    session,
                    append,
                )

                w1 = None
                if is_first_window_pass:  # if first window, use window 1
                    w1 = session.active_window
                    w1.move_window("99")

                start_directory = window_config.get("start_directory", None)

                # If the first pane specifies a start_directory, use that instead.
                panes = window_config["panes"]
                if panes and "start_directory" in panes[0]:
                    start_directory = panes[0]["start_directory"]

                window_shell = window_config.get("window_shell", None)

                # If the first pane specifies a shell, use that instead.
                try:
                    if window_config["panes"][0]["shell"] != "":
                        window_shell = window_config["panes"][0]["shell"]
                except (KeyError, IndexError):
                    pass

                environment = panes[0].get(
                    "environment",
                    window_config.get("environment"),
                )

                window = session.new_window(
                    window_name=window_name,
                    start_directory=start_directory,
                    attach=False,  # do not move to the new window
                    window_index=window_config.get("window_index", ""),
                    window_shell=window_shell,
                    environment=environment,
                )

                if is_first_window_pass:  # if first window, use window 1
                    session.active_window.kill()

            assert isinstance(window, Window)
            window_log = TmuxpLoggerAdapter(
                logger,
                {
                    "tmux_session": session.name or "",
                    "tmux_window": window_name or "",
                },
            )
            window_log.debug("window created")

            if "options" in window_config and isinstance(
                window_config["options"],
                dict,
            ):
                for key, val in window_config["options"].items():
                    window.set_option(key, val)

            if window_config.get("focus"):
                window.select()

            yield window, window_config

    def iter_create_panes(
        self,
        window: Window,
        window_config: dict[str, t.Any],
    ) -> Iterator[t.Any]:
        """Return :class:`libtmux.Pane` iterating through window config dict.

        Run ``shell_command`` with ``$ tmux send-keys``.

        Parameters
        ----------
        window : :class:`libtmux.Window`
            window to create panes for
        window_config : dict
            config section for window

        Returns
        -------
        tuple of (:class:`libtmux.Pane`, ``pane_config``)
            Newly created pane, and the section from the tmuxp configuration
            that was used to create the pane.
        """
        assert isinstance(window, Window)

        pane_base_index = window.show_option("pane-base-index", global_=True)
        assert pane_base_index is not None

        pane = None

        for pane_index, pane_config in enumerate(
            window_config["panes"],
            start=pane_base_index,
        ):
            if self.on_progress:
                self.on_progress(f"Creating pane: {pane_index}")
            if self.on_build_event:
                self.on_build_event(
                    {
                        "event": "pane_creating",
                        "pane_num": pane_index - int(pane_base_index) + 1,
                        "pane_total": len(window_config["panes"]),
                    }
                )

            if pane_index == int(pane_base_index):
                pane = window.active_pane
            else:

                def get_pane_start_directory(
                    pane_config: dict[str, str],
                    window_config: dict[str, str],
                ) -> str | None:
                    if "start_directory" in pane_config:
                        return pane_config["start_directory"]
                    if "start_directory" in window_config:
                        return window_config["start_directory"]
                    return None

                def get_pane_shell(
                    pane_config: dict[str, str],
                    window_config: dict[str, str],
                ) -> str | None:
                    if "shell" in pane_config:
                        return pane_config["shell"]
                    if "window_shell" in window_config:
                        return window_config["window_shell"]
                    return None

                environment = pane_config.get(
                    "environment",
                    window_config.get("environment"),
                )

                assert pane is not None

                pane = pane.split(
                    attach=True,
                    start_directory=get_pane_start_directory(
                        pane_config=pane_config,
                        window_config=window_config,
                    ),
                    shell=get_pane_shell(
                        pane_config=pane_config,
                        window_config=window_config,
                    ),
                    environment=environment,
                )

            assert isinstance(pane, Pane)
            pane_log = TmuxpLoggerAdapter(
                logger,
                {
                    "tmux_session": window.session.name or "",
                    "tmux_window": window.name or "",
                    "tmux_pane": pane.pane_id or "",
                },
            )
            pane_log.debug("pane created")

            # Skip readiness wait when a custom shell/command launcher is set.
            # The shell/window_shell key runs a command (e.g. "top", "sleep 999")
            # that replaces the default shell — the pane exits when the command
            # exits, so there is no interactive prompt to wait for.
            pane_shell = pane_config.get("shell", window_config.get("window_shell"))
            if pane_shell is None:
                _wait_for_pane_ready(pane)

            if "layout" in window_config:
                window.select_layout(window_config["layout"])

            if "suppress_history" in pane_config:
                suppress = pane_config["suppress_history"]
            elif "suppress_history" in window_config:
                suppress = window_config["suppress_history"]
            else:
                suppress = True

            enter = pane_config.get("enter", True)
            sleep_before = pane_config.get("sleep_before", None)
            sleep_after = pane_config.get("sleep_after", None)
            for cmd in pane_config["shell_command"]:
                enter = cmd.get("enter", enter)
                sleep_before = cmd.get("sleep_before", sleep_before)
                sleep_after = cmd.get("sleep_after", sleep_after)

                if sleep_before is not None:
                    time.sleep(sleep_before)

                pane.send_keys(cmd["cmd"], suppress_history=suppress, enter=enter)
                pane_log.debug("sent command %s", cmd["cmd"])

                if sleep_after is not None:
                    time.sleep(sleep_after)

            if pane_config.get("title"):
                pane.set_title(pane_config["title"])

            if pane_config.get("focus"):
                assert pane.pane_id is not None
                window.select_pane(pane.pane_id)

            yield pane, pane_config

    def config_after_window(
        self,
        window: Window,
        window_config: dict[str, t.Any],
    ) -> None:
        """Actions to apply to window after window and pane finished.

        When building a tmux session, sometimes its easier to postpone things
        like setting options until after things are already structurally
        prepared.

        Parameters
        ----------
        window : :class:`libtmux.Window`
            window to create panes for
        window_config : dict
            config section for window
        """
        if "options_after" in window_config and isinstance(
            window_config["options_after"],
            dict,
        ):
            for key, val in window_config["options_after"].items():
                window.set_option(key, val)

        if "shell_command_after" in window_config and isinstance(
            window_config["shell_command_after"],
            dict,
        ):
            for cmd in window_config["shell_command_after"].get("shell_command", []):
                for pane in window.panes:
                    pane.send_keys(cmd["cmd"])

        if window_config.get("clear"):
            for pane in window.panes:
                pane.send_keys("clear", enter=True)

    def find_current_attached_session(self) -> Session:
        """Return current attached session."""
        assert self.server is not None

        current_active_pane = get_current_pane(self.server)

        if current_active_pane is None:
            raise exc.ActiveSessionMissingWorkspaceException

        return next(
            (
                s
                for s in self.server.sessions
                if s.session_id == current_active_pane.session_id
            ),
        )

    def first_window_pass(self, i: int, session: Session, append: bool) -> bool:
        """Return True first window, used when iterating session windows."""
        return len(session.windows) == 1 and i == 1 and not append
