# -*- coding: utf8 - *-
"""
    tmuxp.pane
    ~~~~~~~~~~

    tmuxp helps you manage tmux workspaces.

    :copyright: Copyright 2013 Tony Narlock.
    :license: BSD, see LICENSE for details
"""
from __future__ import absolute_import, division, print_function, with_statement
from . import util, formats
import logging

logger = logging.getLogger(__name__)


class Pane(util.TmuxMappingObject, util.TmuxRelationalObject):

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

        self._pane_id = kwargs['pane_id']

        self.server._update_panes()
        # self.update(**kwargs)

    @property
    def _TMUX(self, *args):

        attrs = {
            'pane_id': self._pane_id
        }

        # from https://github.com/serkanyersen/underscore.py
        def by(val, *args):
            for key, value in attrs.items():
                try:
                    if attrs[key] != val[key]:
                        return False
                except KeyError:
                    return False
                return True

        return list(filter(by, self.server._panes))[0]

    # def __getitem__(self, key):
    #    return

    def tmux(self, *args, **kwargs):
        # if '-t' not in kwargs:
        #    kwargs['-t'] = self.get['session_id']
        return self.server.tmux(*args, **kwargs)

    def send_keys(self, cmd, enter=True):
        '''
            ```tmux send-keys``` to the pane

            :param enter: bool. send enter after sending the key.
        '''
        self.tmux('send-keys', '-t%s' % self.target, cmd)

        if enter:
            self.enter()

    def resize_pane(self, *args, **kwargs):
        '''
            ``$ tmux resize-pane``

        :param target_pane: ``target_pane``, or ``-U``,``-D``, ``-L``, ``-R``.
        :type target_pane: string
        :rtype: :class:`Pane`

        '''
        # if isinstance(target_pane, basestring) and not ':' not in target_pane or isinstance(target_pane, int):
        #    target_pane = "%s.%s" % (self.target, target_pane)

        # logger.error('resize-pane', '-t%s' % self.target)
        if 'height' in kwargs:
            proc = self.tmux('resize-pane', '-t%s' %
                             self.target, '-y%s' % int(kwargs['height']))
        elif 'width' in kwargs:
            proc = self.tmux('resize-pane', '-t%s' %
                             self.target, '-x%s' % int(kwargs['width']))
        else:
            proc = self.tmux('resize-pane', '-t%s' % self.target, args[0])

        if proc.stderr:
            raise Exception(proc.stderr)

        self.server._update_panes()
        return self

    def enter(self):
        '''
            ``$ tmux send-keys`` send Enter to the pane.
        '''
        self.tmux('send-keys', '-t%s' % self.target, 'Enter')

    @property
    def target(self):
        # return "%s:%s.%s" % (self.session.get('session_id'),
        # self.get('window_id'), self.get('pane_index'))
        return self.get('pane_id')

    def __repr__(self):
        return "%s(%s %s)" % (self.__class__.__name__, self.get('pane_id'), self.window)
