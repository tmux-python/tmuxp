# -*- coding: utf8 - *-
"""
    tmuxp.util
    ~~~~~~~~~~

    tmuxp helps you manage tmux workspaces.

    :copyright: Copyright 2013 Tony Narlock.
    :license: BSD, see LICENSE for details
"""
from functools import wraps
from .exc import TmuxNoClientsRunning, TmuxSessionNotFound, ErrorReturnCode_1
from .exc import TmuxNotRunning
from .logxtreme import logging
import unittest
import collections


class TmuxCmd(object):
    """tmux commands can be issued in a variety of ways

    1. outside client: :term:`sh(1)`, targetting last attached client
        a. as ``$ tmux command``. The target will be the most
        recently attached client by default. In cases where the first, only
        session was created created with `-d`, assume that was last attached.

    2. in/outside client, to another server, using :term:`sh(1)`

        This also allows specifying [``-L`` :term:`socket-name`] and
        [``-S`` :term:`socket-path`]. If none is specified it is assumed tmux
        will assume a default socket in ``/tmp``.

    3. inside :term:`control mode` client, by entering command and ``C-m``::

           list-sessions
                >>> %begin 1379042089 2 1
                >>> 25: 1 windows (created Fri Sep 13 11:14:44 2013) [80x24] (attached)
                >>> tmuxp: 1 windows (created Fri Sep 13 10:49:13 2013) [119x24]
                >>> tmuxp_2954: 1 windows (created Fri Sep 13 10:55:18 2013) [80x23]
                >>> %end 1379042089 2 1

    4. inside client: :term:`sh(1)`
       tmux commands will assume the :term:`target` to be the currently
       attached :term:`session`, :term:`window` or :term:`pane`.

    5. inside client: :term:`command-prompt`:

       when inside a tmux client, entering normal commands work.
    """
    pass


def tmux(*args, **kwargs):
    '''
    wraps ``tmux(1) from ``sh`` library in a try-catch.
    '''

    try:
        from sh import tmux as tmuxcall
    except ImportError:
        logging.warning('tmux must be installed and in PATH\'s to use tmuxp')

    try:
        return tmuxcall(*args, **kwargs)
    except ErrorReturnCode_1 as e:
        if e.stderr.startswith('session not found'):
            if 'has-session' in e.full_cmd:
                return e
            else:
                raise TmuxSessionNotFound(e)

        logging.info(e.stderr)
        import traceback
        logging.info(traceback.print_exc())
        if e.stderr.startswith('failed to connect to server'):
            raise TmuxNotRunning(e.stderr)

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

    Uses dunder methods to make TmuxObject sublcasses behave like
    :class:`dict` using ``self._TMUX`` as a datastore for properties.
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
