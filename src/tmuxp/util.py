"""Utility and helper methods for tmuxp."""
import logging
import os
import pathlib
import shlex
import subprocess
import sys
import typing as t

from libtmux._compat import console_to_str

from . import exc

if t.TYPE_CHECKING:
    from libtmux.pane import Pane
    from libtmux.server import Server
    from libtmux.session import Session
    from libtmux.window import Window

logger = logging.getLogger(__name__)

PY2 = sys.version_info[0] == 2


def run_before_script(
    script_file: t.Union[str, pathlib.Path],
    cwd: t.Optional[pathlib.Path] = None,
) -> int:
    """Execute a shell script, wraps :meth:`subprocess.check_call()` in a try/catch."""
    try:
        proc = subprocess.Popen(
            shlex.split(str(script_file)),
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            cwd=cwd,
        )
        if proc.stdout is not None:
            for line in iter(proc.stdout.readline, b""):
                sys.stdout.write(console_to_str(line))
        proc.wait()

        if proc.returncode and proc.stderr is not None:
            stderr = proc.stderr.read()
            proc.stderr.close()
            stderr_strlist = console_to_str(stderr).split("\n")
            stderr_str = "\n".join(list(filter(None, stderr_strlist)))  # filter empty

            raise exc.BeforeLoadScriptError(
                proc.returncode,
                os.path.abspath(script_file),  # NOQA: PTH100
                stderr_str,
            )
        else:
            return proc.returncode
    except OSError as e:
        if e.errno == 2:
            raise exc.BeforeLoadScriptNotExists(
                e,
                os.path.abspath(script_file),  # NOQA: PTH100
            ) from e
        else:
            raise


def oh_my_zsh_auto_title() -> None:
    """Give warning and offer to fix ``DISABLE_AUTO_TITLE``.

    See: https://github.com/robbyrussell/oh-my-zsh/pull/257
    """
    if (
        "SHELL" in os.environ
        and "zsh" in os.environ.get("SHELL", "")
        and os.path.exists(os.path.expanduser("~/.oh-my-zsh"))  # NOQA PTH110, PTH111
        and (
            "DISABLE_AUTO_TITLE" not in os.environ
            or os.environ.get("DISABLE_AUTO_TITLE") == "false"
        )
    ):
        print(
            "Please set:\n\n"
            "\texport DISABLE_AUTO_TITLE='true'\n\n"
            "in ~/.zshrc or where your zsh profile is stored.\n"
            'Remember the "export" at the beginning!\n\n'
            "Then create a new shell or type:\n\n"
            "\t$ source ~/.zshrc",
        )


def get_current_pane(server: "Server") -> t.Optional["Pane"]:
    """Return Pane if one found in env."""
    if os.getenv("TMUX_PANE") is not None:
        try:
            return next(p for p in server.panes if p.pane_id == os.getenv("TMUX_PANE"))
        except StopIteration:
            pass
    return None


def get_session(
    server: "Server",
    session_name: t.Optional[str] = None,
    current_pane: t.Optional["Pane"] = None,
) -> "Session":
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
        raise exc.SessionNotFound() from e

    assert session is not None
    return session


def get_window(
    session: "Session",
    window_name: t.Optional[str] = None,
    current_pane: t.Optional["Pane"] = None,
) -> "Window":
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
        elif current_pane:
            raise exc.WindowNotFound(window_target=str(current_pane)) from e
        raise exc.WindowNotFound() from e

    assert window is not None
    return window


def get_pane(window: "Window", current_pane: t.Optional["Pane"] = None) -> "Pane":
    """Get tmux pane for server by pane name, respects current pane, if passed."""
    pane = None
    try:
        if current_pane is not None:
            pane = window.panes.get(pane_id=current_pane.pane_id)
        else:
            pane = window.attached_pane
    except exc.TmuxpException as e:
        print(e)

    if pane is None:
        if current_pane:
            raise exc.PaneNotFound(str(current_pane))
        raise exc.PaneNotFound()

    return pane
