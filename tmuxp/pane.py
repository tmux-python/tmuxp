# -*- coding: utf8 - *-
"""
    tmuxp.pane
    ~~~~~~~~~~

    tmuxp helps you manage tmux workspaces.

    :copyright: Copyright 2013 Tony Narlock.
    :license: BSD, see LICENSE for details
"""
from .util import live_tmux, TmuxObject, tmux
from .formats import PANE_FORMATS
from .logxtreme import logging


class Pane(TmuxObject):
    '''
        ``tmux(1)`` pane.

        pane holds a psuedoterm and linked to tmux windows.
    '''

    def __init__(self, **kwargs):
        self._session = None
        self._window = None

        self._TMUX = {}
        self.update(**kwargs)

    @classmethod
    def from_tmux(cls, session=None, window=None, **kwargs):
        '''
        Retrieve a tmux pane from server. Returns :class:`Pane`.

        Used for freezing live sessions.

        Iterates ``$ tmux list-panes``, ``-F`` for return formatting.

        :param session: :class:`Session` object.
        :param window: :class:`Window` object.
        '''

        if not session:
            raise ValueError('Pane generated using ``from_tmux`` must have \
                             ``Session`` object')

        if not window:
            raise ValueError('Pane generated using ``from_tmux`` must have \
                             ``Window`` object')

        pane = cls()

        pane.update(**kwargs)

        pane._session = session
        pane._window = window

        return pane

    def send_keys(self, cmd, enter=True):
        '''
            ```tmux send-keys``` to the pane

            :param enter: bool. send enter after sending the key.
        '''
        tmux('send-keys', '-t', int(self.get('pane_index')), cmd)

        if enter:
            self.enter()

    def enter(self):
        '''
            ``$ tmux send-keys`` send Enter to the pane.
        '''
        tmux('send-keys', '-t', int(self.get('pane_index')), 'Enter')

    def __repr__(self):
        # todo test without session_name
        return "%s(%s)" % (self.__class__.__name__, self._window)
