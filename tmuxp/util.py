# -*- coding: utf8 - *-
"""
    tmuxp.util
    ~~~~~~~~~~

    tmuxp helps you manage tmux workspaces.

    :copyright: Copyright 2013 Tony Narlock.
    :license: BSD, see LICENSE for details
"""
from functools import wraps
from .exc import NotRunning, SessionNotFound
from .logxtreme import logging
import unittest
import collections

try:
    from sh import tmux as tmux, ErrorReturnCode_1
except ImportError:
    logging.warning('tmux must be installed and in PATH\'s to use tmuxp')


def live_tmux(f):
    '''
    decorator that checks for one of the 3 unique identifiers in tmux:
    ``pane_id``, ``window_id`` and ``session_id``, found in :class:`Pane`,
    :class:`Window` and :class:`Session` respectively.

    :class:`TmuxObject`, the base class of :class:`Pane`, :class:`Window` and
    :class:`Session` will utilize the :attr:`TmuxObject._TMUX` to store data.

    If a session is imported directly from a configuration or is otherwise
    being built manually via CLI or scripting, :attr:`_TMUX` is populated upon:

    :meth:`Session.new_session` .. ``$ tmux create-session``

    :meth:`Server.list_sessions` .. ``$ tmux list-sessions``

    :meth:`Session.new_window` .. ``$ tmux new-window``

    :meth:`Window.split_window` .. ``$ tmux split-window``
        returns a :class:`Pane` with pane metadata
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


def tmux(*args, **kwargs):
    '''
    wraps ``tmux(1) from ``sh`` library in a try-catch.
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
    :class:`Pane`, :class:`Window` and :class:`Session` which are populated
    with return data from ``tmux (1)`` in the :attr:`._TMUX` dict.

    This is an experimental design choice to just leave ``-F`` commands to give
    _TMUX information, decorate methods to throw an exception if it requires
    interaction with tmux

    With :attr:`_TMUX` :class:`Session` and :class:`Window` can be accessed
    as a property, and the session and window may be looked up dynamically.

    The children inside a ``t`` object are created live. We should look into
    giving them context managers so::

        with Server.select_session(fnmatch):
            # have access to session object
            # note at this level fnmatch may have to be done via python
            # and list-sessions to retrieve object correctly
            session.la()
            with session.attached_window() as window:
                # access to current window
                pass
                with session.find_window(fnmatch) as window:
                    # access to tmux matches window
                    with window.attached_pane() as pane:
                        # access to pane
                        pass
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
