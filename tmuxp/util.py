# -*- coding: utf-8 -*-
"""Utility and helper methods for tmuxp.

tmuxp.util
~~~~~~~~~~

"""
from __future__ import absolute_import, unicode_literals

import logging
import os
import shlex
import subprocess
import sys

from libtmux.exc import LibTmuxException

from . import exc
from ._compat import console_to_str

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
        for line in iter(proc.stdout.readline, b''):
            sys.stdout.write(console_to_str(line))
        proc.wait()

        if proc.returncode:
            stderr = proc.stderr.read()
            proc.stderr.close()
            stderr = console_to_str(stderr).split('\n')
            stderr = '\n'.join(list(filter(None, stderr)))  # filter empty

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

    if 'SHELL' in os.environ and 'zsh' in os.environ.get('SHELL'):
        if os.path.exists(os.path.expanduser('~/.oh-my-zsh')):
            # oh-my-zsh exists
            if (
                'DISABLE_AUTO_TITLE' not in os.environ
                or os.environ.get('DISABLE_AUTO_TITLE') == "false"
            ):
                print(
                    'Please set:\n\n'
                    '\texport DISABLE_AUTO_TITLE=\'true\'\n\n'
                    'in ~/.zshrc or where your zsh profile is stored.\n'
                    'Remember the "export" at the beginning!\n\n'
                    'Then create a new shell or type:\n\n'
                    '\t$ source ~/.zshrc'
                )


def raise_if_tmux_not_running(server):
    """Raise exception if not running. More descriptive error if no server found."""
    try:
        server.sessions
    except LibTmuxException as e:
        if any(
            needle in str(e)
            for needle in ['No such file or directory', 'no server running on']
        ):
            raise LibTmuxException(
                'no tmux session found. Start a tmux session and try again. \n'
                'Original error: ' + str(e)
            )
        else:
            raise e


def get_current_pane(server):
    """Return Pane if one found in env"""
    if os.getenv('TMUX_PANE') is not None:
        try:
            return [
                p
                for p in server._list_panes()
                if p.get('pane_id') == os.getenv('TMUX_PANE')
            ][0]
        except IndexError:
            pass


def get_session(server, session_name=None, current_pane=None):
    if session_name:
        session = server.find_where({'session_name': session_name})
    elif current_pane is not None:
        session = server.find_where({'session_id': current_pane['session_id']})
    else:
        session = server.list_sessions()[0]

    if not session:
        raise exc.TmuxpException('Session not found: %s' % session_name)

    return session


def get_window(session, window_name=None, current_pane=None):
    if window_name:
        window = session.find_where({'window_name': window_name})
        if not window:
            raise exc.TmuxpException('Window not found: %s' % window_name)
    elif current_pane is not None:
        window = session.find_where({'window_id': current_pane['window_id']})
    else:
        window = session.list_windows()[0]

    return window


def get_pane(window, current_pane=None):
    try:
        if current_pane is not None:
            pane = window.find_where({'pane_id': current_pane['pane_id']})  # NOQA: F841
        else:
            pane = window.attached_pane  # NOQA: F841
    except exc.TmuxpException as e:
        print(e)
        return

    return pane
