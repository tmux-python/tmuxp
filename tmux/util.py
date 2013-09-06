# -*- coding: utf8 - *-
"""
    tmuxwrapper.util
    ~~~~~~~~~~~~~~~~

    tmuxwrapper helps you manage tmux workspaces.

    :copyright: Copyright 2013 Tony Narlock <tony@git-pull.com>.
    :license: BSD, see LICENSE for details
"""
from functools import wraps
from sh import ErrorReturnCode_1
from .exc import NotRunning, SessionNotFound
from .logxtreme import logging
import unittest


def live_tmux(f):
    '''
    decorator that checks for :attrib:`_TMUX` inside :class:`Session`,
    :class:`Window` and :class:`Pane` objects.

    :attrib:`_TMUX` stores valuable information for an tmux object's life
    cycle. Hereinafter, I will call this ``MetaData``

    ``tmux( returns information

    @todo: in the future, :class:`Pane` will have ``PANE_FORMATS``,
    ``WINDOW_FORMATS`` and ``Session_FORMATS`` metadata, and :class:`Window`
    will have ``WINDOW_FORMATS`` and ``Session_FORMATS`` If a :attrib:`_TMUX
    exists, it should be possible to do a lookup for its parent :class:`Window`
    or :class:`Pane` object.

    Because this data is live in the system, caching strategy isn't a priority.

    If a session is imported directly from a configuration or is otherwise
    being built manually via CLI or scripting, :attrib:`_TMUX` is populated
    when:

    A tmux session is created with:

    :meth:`Session.create_session` aka ``tmux create-session``

    :meth:`Server.list_sessions` aka ``tmux list-sessions``
    :meth:`Session.new_window` aka ``tmux new-window``
    :meth:`Window.split_window` aka ``tmux split-window``
        returns a :class:`Pane` with pane metadata

        - its first :class:`Window`, in :attrib:`_windows`, and subsequently,
          and the :class:`Window`'s first :class:`Pane` in :attrib:`_panes`
          is populated with :attrib:`_TMUX` This is returned because the

            attributes.
        - a window is created with :meth:`Session.create_session`
    '''
    @wraps(f)
    def live_tmux(self, *args, **kwargs):
        if any(key in self for key in ('pane_id', 'window_id', 'session_id')):
            return f(self, *args, **kwargs)
        else:
            raise NotRunning(
                "self._TMUX not found, this object is not part of an active"
                "tmux session. If you need help please post an issue on github"
            )
    return live_tmux


def tmuxa(*args, **kwargs):
    '''
    wrap tmux from ``sh`` library in a try catch
    '''
    try:
        #return tmx(*args, **kwargs)
        pass
    except ErrorReturnCode_1 as e:

        if e.stderr.startswith('session not found'):
            raise SessionNotFound('session not found')

        logging.error(
            "\n\tcmd:\t%s\n"
            "\terror:\t%s"
            % (e.full_cmd, e.stderr)
        )
        return e.stderr
