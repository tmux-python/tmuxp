"""Create a tmux workspace from a workspace :py:obj:`dict`."""

import logging
import os
import shutil
import time
import typing as t

from libtmux._internal.query_list import ObjectDoesNotExist
from libtmux.common import has_gte_version, has_lt_version
from libtmux.pane import Pane
from libtmux.server import Server
from libtmux.session import Session
from libtmux.window import Window

from tmuxp import exc
from tmuxp.util import get_current_pane, run_before_script

logger = logging.getLogger(__name__)

COLUMNS_FALLBACK = 80


def get_default_columns() -> int:
    """Return default session column size use when building new tmux sessions."""
    return int(
        os.getenv("TMUXP_DEFAULT_COLUMNS", os.getenv("COLUMNS", COLUMNS_FALLBACK))
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

    The normal phase of loading is:

    1. Load JSON / YAML file via via :class:`pathlib.Path`::

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

    server: "Server"
    _session: t.Optional["Session"]
    session_name: str

    def __init__(
        self,
        session_config: t.Dict[str, t.Any],
        server: Server,
        plugins: t.Optional[t.List[t.Any]] = None,
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

    def build(self, session: t.Optional[Session] = None, append: bool = False) -> None:
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
        """
        if not session:
            if not self.server:
                raise exc.TmuxpException(
                    "WorkspaceBuilder.build requires server to be passed "
                    + "on initialization, or pass in session object to here.",
                )
            new_session_kwargs = {}
            if "start_directory" in self.session_config:
                new_session_kwargs["start_directory"] = self.session_config[
                    "start_directory"
                ]

            if (
                has_gte_version("2.6")
                and os.getenv("TMUXP_DETECT_TERMINAL_SIZE", "1") == "1"
            ):
                terminal_size = shutil.get_terminal_size(
                    fallback=(get_default_columns(), get_default_rows())
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

        self._session = session

        assert session.server is not None

        self.server: "Server" = session.server
        assert self.server.sessions is not None
        assert self.server.has_session(session.name)
        assert session.id

        assert isinstance(session, Session)

        for plugin in self.plugins:
            plugin.before_workspace_builder(self.session)

        focus = None

        if "before_script" in self.session_config:
            try:
                cwd = None

                # we want to run the before_script file cwd'd from the
                # session start directory, if it exists.
                if "start_directory" in self.session_config:
                    cwd = self.session_config["start_directory"]
                run_before_script(self.session_config["before_script"], cwd=cwd)
            except Exception:
                self.session.kill()
                raise

        if "options" in self.session_config:
            for option, value in self.session_config["options"].items():
                self.session.set_option(option, value)

        if "global_options" in self.session_config:
            for option, value in self.session_config["global_options"].items():
                self.session.set_option(option, value, _global=True)

        if "environment" in self.session_config:
            for option, value in self.session_config["environment"].items():
                self.session.set_environment(option, value)

        for window, window_config in self.iter_create_windows(session, append):
            assert isinstance(window, Window)

            for plugin in self.plugins:
                plugin.on_window_create(window)

            focus_pane = None
            for pane, pane_config in self.iter_create_panes(window, window_config):
                assert isinstance(pane, Pane)
                pane = pane

                if "layout" in window_config:
                    window.select_layout(window_config["layout"])

                if pane_config.get("focus"):
                    focus_pane = pane

            if window_config.get("focus"):
                focus = window

            self.config_after_window(window, window_config)

            for plugin in self.plugins:
                plugin.after_window_finished(window)

            if focus_pane:
                focus_pane.select()

        if focus:
            focus.select()

    def iter_create_windows(
        self,
        session: Session,
        append: bool = False,
    ) -> t.Iterator[t.Any]:
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

            environment = panes[0].get("environment", window_config.get("environment"))
            if environment and has_lt_version("3.0"):
                # Falling back to use the environment of the first pane for the window
                # creation is nice but yields misleading error messages.
                pane_env = panes[0].get("environment")
                win_env = window_config.get("environment")
                if pane_env and win_env:
                    target = "panes and windows"
                elif pane_env:
                    target = "panes"
                else:
                    target = "windows"
                logger.warning(
                    f"Cannot set environment for new {target}. "
                    "You need tmux 3.0 or newer for this.",
                )
                environment = None

            window = session.new_window(
                window_name=window_name,
                start_directory=start_directory,
                attach=False,  # do not move to the new window
                window_index=window_config.get("window_index", ""),
                window_shell=window_shell,
                environment=environment,
            )
            assert isinstance(window, Window)

            if is_first_window_pass:  # if first window, use window 1
                session.active_window.kill()

            if "options" in window_config and isinstance(
                window_config["options"],
                dict,
            ):
                for key, val in window_config["options"].items():
                    window.set_window_option(key, val)

            if window_config.get("focus"):
                window.select()

            yield window, window_config

    def iter_create_panes(
        self,
        window: Window,
        window_config: t.Dict[str, t.Any],
    ) -> t.Iterator[t.Any]:
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

        pane_base_index_str = window.show_window_option("pane-base-index", g=True)
        assert pane_base_index_str is not None
        pane_base_index = int(pane_base_index_str)

        pane = None

        for pane_index, pane_config in enumerate(
            window_config["panes"],
            start=pane_base_index,
        ):
            if pane_index == int(pane_base_index):
                pane = window.active_pane
            else:

                def get_pane_start_directory(
                    pane_config: t.Dict[str, str],
                    window_config: t.Dict[str, str],
                ) -> t.Optional[str]:
                    if "start_directory" in pane_config:
                        return pane_config["start_directory"]
                    if "start_directory" in window_config:
                        return window_config["start_directory"]
                    return None

                def get_pane_shell(
                    pane_config: t.Dict[str, str],
                    window_config: t.Dict[str, str],
                ) -> t.Optional[str]:
                    if "shell" in pane_config:
                        return pane_config["shell"]
                    if "window_shell" in window_config:
                        return window_config["window_shell"]
                    return None

                environment = pane_config.get(
                    "environment",
                    window_config.get("environment"),
                )
                if environment and has_lt_version("3.0"):
                    # Just issue a warning when the environment comes from the pane
                    # configuration as a warning for the window was already issued when
                    # the window was created.
                    if pane_config.get("environment"):
                        logger.warning(
                            "Cannot set environment for new panes. "
                            "You need tmux 3.0 or newer for this.",
                        )
                    environment = None

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

                if sleep_after is not None:
                    time.sleep(sleep_after)

            if pane_config.get("focus"):
                assert pane.pane_id is not None
                window.select_pane(pane.pane_id)

            yield pane, pane_config

    def config_after_window(
        self,
        window: Window,
        window_config: t.Dict[str, t.Any],
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
                window.set_window_option(key, val)

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
