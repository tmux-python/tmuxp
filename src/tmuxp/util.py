"""Utility and helper methods for tmuxp."""

from __future__ import annotations

import logging
import os
import shlex
import subprocess
import sys
import typing as t

from . import exc

if t.TYPE_CHECKING:
    import pathlib

    from libtmux.pane import Pane
    from libtmux.server import Server
    from libtmux.session import Session
    from libtmux.window import Window

logger = logging.getLogger(__name__)

PY2 = sys.version_info[0] == 2


def run_before_script(
    script_file: str | pathlib.Path,
    cwd: pathlib.Path | None = None,
) -> int:
    """Execute shell script, ``tee``-ing output to both terminal (if TTY) and buffer."""
    script_cmd = shlex.split(str(script_file))

    try:
        proc = subprocess.Popen(
            script_cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,  # decode to str
            errors="backslashreplace",
        )
    except FileNotFoundError as e:
        raise exc.BeforeLoadScriptNotExists(
            e,
            os.path.abspath(script_file),  # NOQA: PTH100
        ) from e

    out_buffer = []
    err_buffer = []

    # While process is running, read lines from stdout/stderr
    # and write them to this process's stdout/stderr if isatty
    is_out_tty = sys.stdout.isatty()
    is_err_tty = sys.stderr.isatty()

    # You can do a simple loop reading in real-time:
    while True:
        # Use .poll() to check if the child has exited
        return_code = proc.poll()

        # Read one line from stdout, if available
        line_out = proc.stdout.readline() if proc.stdout else ""

        # Read one line from stderr, if available
        line_err = proc.stderr.readline() if proc.stderr else ""

        if line_out and line_out.strip():
            out_buffer.append(line_out)
            if is_out_tty:
                sys.stdout.write(line_out)
                sys.stdout.flush()

        if line_err and line_err.strip():
            err_buffer.append(line_err)
            if is_err_tty:
                sys.stderr.write(line_err)
                sys.stderr.flush()

        # If no more data from pipes and process ended, break
        if not line_out and not line_err and return_code is not None:
            break

    # At this point, the process has finished
    return_code = proc.wait()

    if return_code != 0:
        # Join captured stderr lines for your exception
        stderr_str = "".join(err_buffer).strip()
        raise exc.BeforeLoadScriptError(
            return_code,
            os.path.abspath(script_file),  # NOQA: PTH100
            stderr_str,
        )

    return return_code


def oh_my_zsh_auto_title() -> None:
    """Give warning and offer to fix ``DISABLE_AUTO_TITLE``.

    See: https://github.com/robbyrussell/oh-my-zsh/pull/257
    """
    if (
        "SHELL" in os.environ
        and "zsh" in os.environ.get("SHELL", "")
        and os.path.exists(os.path.expanduser("~/.oh-my-zsh"))  # NOQA: PTH110, PTH111
        and (
            "DISABLE_AUTO_TITLE" not in os.environ
            or os.environ.get("DISABLE_AUTO_TITLE") == "false"
        )
    ):
        print(  # NOQA: T201 RUF100
            "Please set:\n\n"
            "\texport DISABLE_AUTO_TITLE='true'\n\n"
            "in ~/.zshrc or where your zsh profile is stored.\n"
            'Remember the "export" at the beginning!\n\n'
            "Then create a new shell or type:\n\n"
            "\t$ source ~/.zshrc",
        )


def get_current_pane(server: Server) -> Pane | None:
    """Return Pane if one found in env."""
    if os.getenv("TMUX_PANE") is not None:
        try:
            return next(p for p in server.panes if p.pane_id == os.getenv("TMUX_PANE"))
        except StopIteration:
            pass
    return None


def get_session(
    server: Server,
    session_name: str | None = None,
    current_pane: Pane | None = None,
) -> Session:
    """Get tmux session for server by session name, respects current pane, if passed."""
    try:
        if session_name:
            session = server.sessions.get(session_name=session_name)
        elif current_pane is not None:
            session = server.sessions.get(session_id=current_pane.session_id)
        else:
            current_pane = get_current_pane(server)
            if current_pane:
                session = server.sessions.get(session_id=current_pane.session_id)
            else:
                session = server.sessions[0]

    except Exception as e:
        if session_name:
            raise exc.SessionNotFound(session_name) from e
        raise exc.SessionNotFound from e

    assert session is not None
    return session


def get_window(
    session: Session,
    window_name: str | None = None,
    current_pane: Pane | None = None,
) -> Window:
    """Get tmux window for server by window name, respects current pane, if passed."""
    try:
        if window_name:
            window = session.windows.get(window_name=window_name)
        elif current_pane is not None:
            window = session.windows.get(window_id=current_pane.window_id)
        else:
            window = session.windows[0]
    except Exception as e:
        if window_name:
            raise exc.WindowNotFound(window_target=window_name) from e
        if current_pane:
            raise exc.WindowNotFound(window_target=str(current_pane)) from e
        raise exc.WindowNotFound from e

    assert window is not None
    return window


def get_pane(window: Window, current_pane: Pane | None = None) -> Pane:
    """Get tmux pane for server by pane name, respects current pane, if passed."""
    pane = None
    try:
        if current_pane is not None:
            pane = window.panes.get(pane_id=current_pane.pane_id)
        else:
            pane = window.active_pane
    except exc.TmuxpException as e:
        print(e)  # NOQA: T201 RUF100

    if pane is None:
        if current_pane:
            raise exc.PaneNotFound(str(current_pane))
        raise exc.PaneNotFound

    return pane
