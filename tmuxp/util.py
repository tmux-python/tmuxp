# -*- coding: utf8 - *-
"""
    tmuxp.util
    ~~~~~~~~~~

    tmuxp helps you manage tmux workspaces.

    :copyright: Copyright 2013 Tony Narlock.
    :license: BSD, see LICENSE for details
"""
from __future__ import absolute_import, division, print_function, with_statement

from functools import wraps
from .exc import TmuxNoClientsRunning, TmuxSessionNotFound
from .exc import TmuxNotRunning
import unittest
import collections
import subprocess

from . import log
import logging

logger = logging.getLogger(__name__)


class tmux(object):
    ''':py:mod:`subprocess` for :ref:`tmux(1)`.

    Usage:

    .. code-block:: python

        tmux('new-session', '-s%' % 'my session')

    Equivalent to:

    .. code-block:: bash

        $ tmux new-session -s my session
    '''

    def __init__(self, *args, **kwargs):
        cmd = ['tmux']
        cmd += args  # add the command arguments to cmd
        cmd = [str(c) for c in cmd]

        self.cmd = cmd

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.process.wait()
            stdout, stderr = self.process.stdout.read(), self.process.stderr.read()
        except Exception as e:
            logger.error('Exception for %s: \n%s' % (
                cmd,
                #' '.join([str(c) for c in cmd]),
                e.message)
            )
        self.stdout = stdout.split('\n')
        self.stdout = filter(None, self.stdout)  # filter empty values

        self.stderr = stderr.split('\n')
        self.stderr = filter(None, self.stderr)  # filter empty values

        if 'has-session' in cmd and len(self.stderr):
            if not self.stdout:
                self.stdout = self.stderr[0]

        logging.debug('self.stdout for %s: \n%s' % (' '.join(cmd), self.stdout))


class TmuxObject(collections.MutableMapping):
    '''
    Base: :py:class:`collections.MutableMapping`

    Base class for of :class:`Pane`, :class:`Window` and :class:`Session`.

    The mapping uses attribute ``._TMUX`` to store values.
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


class TmuxObjectDiff(object):
    ''' Methods for updating the child objects and still keeping the
        objects intact if they exist.

        @todo

        - make more generic / backbone-like by allow an 'id' property, such
        as ``window_id`` being ``id`` for :class:`Window`.
        - change :meth:`Server.list_session`, :meth:`Session.list_windows`,
        :meth:`Window.list_panes` to call `list_children` in here.

        The _list_sessions, _list_windows, _list_panes can retrieve a list of
        dict from the Popen of tmux, then pass it into here.
    '''

    def set(self, object):
        '''
        add a or a :obj:`list` of sessions, panes or windows to the object.

        this is subclassed by:

            - :class:`Server` to hold :class:`Session` objects.
            - :class:`Session` to hold :class:`Window` objects.
            - :class:`Window` to hold :class:`Pane` objects.

        if a list object is entered, use this recursively

        :param: object: any sibling of :class:`TmuxObject`: :class:`Session`,
        :class:`Window`, :class:`Pane`.
        '''
