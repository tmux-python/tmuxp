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
import collections


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


class TmuxObject(collections.MutableMapping):
    '''
    Panes, Windows and Sessions which are populated with return data from
    ``tmux(1)`` in the .tmux dict.

    This is an experimental design choice to just leave `-F` commands to give
    _TMUX information, decorate methods to throw an exception if it requires
    interaction with tmux

    With :attrib:`._TMUX` :class:`Session` and :class:`Window` can be accessed
    as a property, and the session and window may be looked up dynamically.

    The children inside a ``t`` object are created live. We should look into
    giving them context managers so::

        >>>     with Server.select_session(fnmatch):
        >>>     # have access to session object
        >>>         # note at this level fnmatch may have to be done via python
        >>>         # and list-sessions to retrieve object correctly
        >>>         session.la()
        >>>     with session.attached_window() as window:
        >>>         # access to current window
        >>>         pass
        >>>     with session.find_window(fnmatch) as window:
        >>>         # access to tmux matches window
        >>>         with window.attached_pane() as pane:
        >>>             # access to pane
        >>>             pass
    '''
    def __getitem__(self, key):
        return self._TMUX[key]

    def __setitem__(self, key, value):
        self._TMUX[key] = value
        self.dirty = True

    def __delitem__(self, key):
        del self._TMUX[key]
        self.dirty = True

    def keys(self):
        return self._TMUX.keys()

    def __iter__(self):
        return self._TMUX.__iter__()

    def __len__(self):
        return len(self._TMUX.keys())


class ConfigExpand(object):

    def __init__(self, config):
        self.config = config

    def expand(self):
        return self.expand_shell_command()

    def expand_shell_command(self):
        '''
        iterate through session, windows, and panes for ``shell_command``, if
        it is a string, turn to list.
        '''
        config = self.config

        def _expand(c):
            '''any config section, session, window, pane that can
            contain the 'shell_command' value
            '''
            if ('shell_command' in c and
                    isinstance(c['shell_command'], basestring)):
                    c['shell_command'] = [c['shell_command']]

            return c

        config = _expand(config)
        for window in config['windows']:
            window = _expand(window)
            window['panes'] = [_expand(pane) for pane in window['panes']]

        return config
