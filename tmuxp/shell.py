# -*- coding: utf-8 -*-
"""Command line tool for managing tmux workspaces and tmuxp configurations.

tmuxp.shell
~~~~~~~~~~~

"""
from __future__ import absolute_import

import logging
import os

from libtmux.exc import LibTmuxException

from . import exc

logger = logging.getLogger(__name__)


def raise_if_tmux_not_running(server):
    """Raise exception if not running. More descriptive error if no server found."""
    try:
        server.sessions
    except LibTmuxException as e:
        if 'No such file or directory' in str(e):
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
