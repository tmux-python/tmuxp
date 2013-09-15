# -*- coding: utf8 - *-
"""
    tmuxp.pane
    ~~~~~~~~~~

    tmuxp helps you manage tmux workspaces.

    :copyright: Copyright 2013 Tony Narlock.
    :license: BSD, see LICENSE for details
"""
from .util import TmuxObject
from .formats import PANE_FORMATS
from .logxtreme import logging


class Pane(TmuxObject):
    '''
        ``tmux(1)`` pane.

        pane holds a psuedoterm and linked to tmux windows.

        Retrieve a tmux pane from server. Returns :class:`Pane`.

        Iterates ``$ tmux list-panes``, ``-F`` for return formatting.

        :param session: :class:`Session` object.
        :param window: :class:`Window` object.

    '''

    def __init__(self, window=None, **kwargs):
        if not window:
            raise ValueError('Pane must have \
                             ``Window`` object')

        self.window = window
        self.session = self.window.session
        self.server = self.session.server

        self._TMUX = {}
        self.update(**kwargs)

    def tmux(self, *args, **kwargs):
        #if '-t' not in kwargs:
        #    kwargs['-t'] = self.get['session_id']
        return self.server.tmux(*args, **kwargs)

    def send_keys(self, cmd, enter=True):
        '''
            ```tmux send-keys``` to the pane

            :param enter: bool. send enter after sending the key.
        '''
        self.tmux('send-keys', '-t', self.target, cmd)

        if enter:
            self.enter()

    def enter(self):
        '''
            ``$ tmux send-keys`` send Enter to the pane.
        '''
        self.tmux('send-keys', '-t', self.target, 'Enter')

    @property
    def target(self):
        return "%s:%s.%s" % (self.session.get('session_id'), self.get('window_id'), int(self.get('pane_index')))

    def __repr__(self):
        # todo test without session_name
        return "%s(%s %s)" % (self.__class__.__name__, self.get('pane_id'), self.window)
