"""Utility and helper methods for tmuxp.

tmuxp.util
~~~~~~~~~~

"""
import logging
import os
import shlex
import subprocess
import sys

from libtmux._compat import console_to_str

from . import exc

logger = logging.getLogger(__name__)

PY2 = sys.version_info[0] == 2


def run_before_script(script_file, cwd=None):
    """Function to wrap try/except for subprocess.check_call()."""
    try:
        proc = subprocess.Popen(
            shlex.split(str(script_file)),
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            cwd=cwd,
        )
        for line in iter(proc.stdout.readline, b""):
            sys.stdout.write(console_to_str(line))
        proc.wait()

        if proc.returncode:
            stderr = proc.stderr.read()
            proc.stderr.close()
            stderr = console_to_str(stderr).split("\n")
            stderr = "\n".join(list(filter(None, stderr)))  # filter empty

            raise exc.BeforeLoadScriptError(
                proc.returncode, os.path.abspath(script_file), stderr
            )

        return proc.returncode
    except OSError as e:
        if e.errno == 2:
            raise exc.BeforeLoadScriptNotExists(e, os.path.abspath(script_file))
        else:
            raise e


def oh_my_zsh_auto_title():
    """Give warning and offer to fix ``DISABLE_AUTO_TITLE``.

    see: https://github.com/robbyrussell/oh-my-zsh/pull/257

    """

    if "SHELL" in os.environ and "zsh" in os.environ.get("SHELL"):
        if os.path.exists(os.path.expanduser("~/.oh-my-zsh")):
            # oh-my-zsh exists
            if (
                "DISABLE_AUTO_TITLE" not in os.environ
                or os.environ.get("DISABLE_AUTO_TITLE") == "false"
            ):
                print(
                    "Please set:\n\n"
                    "\texport DISABLE_AUTO_TITLE='true'\n\n"
                    "in ~/.zshrc or where your zsh profile is stored.\n"
                    'Remember the "export" at the beginning!\n\n'
                    "Then create a new shell or type:\n\n"
                    "\t$ source ~/.zshrc"
                )


def get_current_pane(server):
    """Return Pane if one found in env"""
    if os.getenv("TMUX_PANE") is not None:
        try:
            return [p for p in server.panes if p.pane_id == os.getenv("TMUX_PANE")][0]
        except IndexError:
            pass


def get_session(server, session_name=None, current_pane=None):
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
    except Exception:
        session = None

    if session is None:
        if session_name:
            raise exc.TmuxpException("Session not found: %s" % session_name)
        else:
            raise exc.TmuxpException("Session not found")

    return session


def get_window(session, window_name=None, current_pane=None):
    try:
        if window_name:
            window = session.windows.get(window_name=window_name)
        elif current_pane is not None:
            window = session.windows.get(window_id=current_pane.window_id)
        else:
            window = session.windows[0]
    except Exception:
        window = None

    if window is None:
        if window_name:
            raise exc.TmuxpException("Window not found: %s" % window_name)
        if current_pane:
            raise exc.TmuxpException("Window not found: %s" % current_pane)
        else:
            raise exc.TmuxpException("Window not found")

    return window


def get_pane(window, current_pane=None):
    try:
        if current_pane is not None:
            pane = window.panes.get(pane_id=current_pane.pane_id)  # NOQA: F841
        else:
            pane = window.attached_pane  # NOQA: F841
    except exc.TmuxpException as e:
        print(e)
        return

    if pane is None:
        if current_pane:
            raise exc.TmuxpException("Pane not found: %s" % current_pane)
        else:
            raise exc.TmuxpException("Pane not found")

    return pane
