# -*- coding: utf8 - *-
"""
    tmuxp.session
    ~~~~~~~~~~~~~

    tmuxp helps you manage tmux workspaces.

    :copyright: Copyright 2013 Tony Narlock.
    :license: BSD, see LICENSE for details
"""
from __future__ import absolute_import, division, print_function, with_statement

import pipes
from .window import Window
from .exc import TmuxSessionExists
from . import util, formats
import logging
logger = logging.getLogger(__name__)


class Session(util.TmuxMappingObject, util.TmuxRelationalObject):

    '''
    ``tmux(1) session``.

    Holds :class:`Window` objects.

    '''

    childIdAttribute = 'window_id'

    def __init__(self, server=None, **kwargs):

        self.server = server

        if not 'session_id' in kwargs:
            raise ValueError('Session requires a `session_id`')
        self._session_id = kwargs['session_id']

        self.server._update_windows()

    @property
    def _TMUX(self, *args):

        attrs = {
            'session_id': str(self._session_id)
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

        try:
            return list(filter(by, self.server._sessions))[0]
        except IndexError as e:
            logger.error(e)
            logger.error(self._session_name)
            logger.error(self.server._sessions)

    def tmux(self, *args, **kwargs):
        # if '-t' not in kwargs:
        #    kwargs['-t'] = self.get['session_id']
        return self.server.tmux(*args, **kwargs)

    def attach_session(self, target_session=None):
        '''
        ``$ tmux attach-session`` aka alias: ``$ tmux attach``

        :param: target_session: str. name of the session. fnmatch(3) works.
        '''
        proc = self.tmux('attach-session', '-t%s' % self.get('session_id'))

        if proc.stderr:
            raise Exception(proc.stderr)

    def kill_session(self, target_session=None):
        '''
        ``$ tmux kill-session``

        :param: target_session: str. note this accepts fnmatch(3). 'asdf' will
                                kill asdfasd
        '''
        proc = self.tmux('kill-session', '-t%s' % self.get('session_id'))

        if proc.stderr:
            raise Exception(proc.stderr)

    def switch_client(self, target_session=None):
        '''
        ``$ tmux kill-session``

        :param: target_session: str. note this accepts fnmatch(3). 'asdf' will
                                kill asdfasd
        '''
        proc = self.tmux('switch-client', '-t%s' % self.get('session_id'))

        if proc.stderr:
            raise Exception(proc.stderr)


    def rename_session(self, new_name):
        '''rename session and return new :class:`Session` object

        :param rename_session: new session name
        :type rename_session: string
        '''
        new_name = pipes.quote(new_name)
        proc = self.tmux(
            'rename-session',
            '-t%s' % self.get('session_id'),
            new_name
        )

        if proc.stderr:
            raise Exception(proc.stderr)

        return self

    def new_window(self,
                   window_name=None,
                   automatic_rename=False,
                   attach=True):
        '''
        ``$ tmux new-window``

        .. note::

            By default, this will make the window active. For the new window
            to be created and not set to current, pass in ``attach=False``.

        :param window_name: window name.

        .. code-block:: bash

            $ tmux new-window -n <window_name>

        :type window_name: string

        :param automatic_rename: assume automatic_rename if no window_name.
        :type automatic_rename: bool

        :param attach: make new window the current window after creating it,
                       default True.
        :param type: bool
        '''
        wformats = ['session_name', 'session_id'] + formats.WINDOW_FORMATS
        tmux_formats = ['#{%s}' % f for f in wformats]

        window_args = (
            '-t%s' % self.get('session_id'),
            '-P',
            '-F%s' % '\t'.join(tmux_formats),  # output
        )

        if window_name:
            window_args += ('-n', window_name)

        if not attach:
            window_args += ('-d',)

        proc = self.tmux('new-window', *window_args)

        if proc.stderr:
            raise Exception(proc.stderr)

        window = proc.stdout[0]

        window = dict(zip(wformats, window.split('\t')))

        # clear up empty dict
        window = dict((k, v) for k, v in window.items() if v)
        window = Window(session=self, **window)

        if automatic_rename:
            window.set_window_option('automatic-rename', True)

        self.server._update_windows()

        return window

    def kill_window(self, target_window=None):
        '''
        ``$ tmux kill-window``

        Kill the current window or the window at ``target-window``. removing it
        from any sessions to which it is linked.

        :param target_window: the ``target window``.
        :type target_window: string
        '''

        tmux_args = list()

        if target_window:
            if isinstance(target_window, int):
                target = '-t%s:%d' % (self.get('session_name'), target_window)
            else:
                target = '-t%s' % target_window

        proc = self.tmux('kill-window', target)

        if proc.stderr:
            raise Exception(proc.stderr)

        self.server._update_windows()

    def _list_windows(self):
        windows = self.server._update_windows()._windows

        windows = [
            w for w in windows if w['session_id'] == self.get('session_id')
        ]

        return windows

    @property
    def _windows(self):
        return self._list_windows()

    def list_windows(self):
        '''
        Return a list of :class:`Window` from the ``tmux(1)`` session.

        :rtype: :class:`Window`
        '''
        windows = [
            w for w in self._windows if w['session_id'] == self._session_id
        ]

        return [Window(session=self, **window) for window in windows]

    @property
    def windows(self):
        return self.list_windows()
    children = windows

    def attached_window(self):
        '''
            Returns active :class:`Window` object.
        '''
        active_windows = []
        for window in self._windows:
            if 'window_active' in window:
                # for now window_active is a unicode
                if window.get('window_active') == '1':
                    active_windows.append(Window(session=self, **window))
                else:
                    continue

        if len(active_windows) == 1:
            return active_windows[0]
        else:
            raise Exception(
                'multiple active windows found. %s' % active_windows)

        if len(self._windows) == 0:
            raise Exception('No Windows')

        return False

    def select_window(self, target_window):
        '''
            ``$ tmux select-window``

            :param: window: ``target_window`` also 'last-window' (``-l``),
                            'next-window' (``-n``), or 'previous-window' (``-p``)
            :type window: integer

            Returns the attached :class:`Window`.

            Todo: assure ``-l``, ``-n``, ``-p`` work.
        '''
        # if isinstance(target_window, int):
            # target = '-t%s:%s' % (self.get('session_name'), target_window)
        # elif isinstance(target_window, basestring):
            # target = '-t%s:%s' % (self.get('session_name'), target_window)
        # else:
            # target = '-t%s' % target_window

        target = '-t%s' % target_window

        proc = self.tmux('select-window', target)

        if proc.stderr:
            raise Exception(proc.stderr)

        return self.attached_window()

    def attached_pane(self):
        '''
            Returns active :class:`Pane` object
        '''
        return self.attached_window().attached_pane()

    def is_clean(self):
        ''' check if current session is pure, untouched:

            - 1 window
            - 1 pane, no history.

            returns True or False.
        '''
        if (len(self._windows) > 1):
            logger.debug('%s not clean, multiple windows', self)
            return False

        if (len(self.attached_window()._panes) > 1):
            logger.debug('%s not clean, multiple panes (%s)' % (
                self, len(self.attached_window()._panes)))
            return False

        if (int(self.attached_window().attached_pane().get('history_size')) > 0):
            logger.debug('%s history_size (%s), greater than 0' % (
                self, self.attached_window().attached_pane().get('history_size')))
            return False

        return True

    def set_option(self, option, value):
        '''
        wrapper for ``tmux(1)``::

            $ tmux set-option <option> <value>

        todo: needs tests

        :param option: the window option. such as 'default-shell'.
        :type option: string
        :param value: window value. True/False will turn in 'on' and 'off'.
        :type value: string or bool
        '''

        if isinstance(value, bool) and value:
            value = 'on'
        elif isinstance(value, bool) and not value:
            value = 'off'

        process = self.tmux(
            'set-option', option, value
        )

        if process.stderr:
            if isinstance(process.stderr, list) and len(process.stderr) == int(1):
                process.stderr = process.stderr[0]
            raise ValueError('tmux set-option stderr: %s' % process.stderr)

    def show_options(self, option=None):
        '''
        return a dict of options for the window.

        For familiarity with tmux, the option ``option`` param forwards to pick
        a single option, forwarding to :meth:`Session.show_option`.

        :param option: optional. show a single option.
        :type option: string
        :rtype: :py:obj:`dict`
        '''

        if option:
            return self.show_option(option)
        else:
            session_options = self.tmux(
                'show-options'
            ).stdout

        session_options = [tuple(item.split(' ')) for item in session_options]

        session_options = dict(session_options)

        for key, value in session_options.items():
            if value.isdigit():
                session_options[key] = int(value)

        return session_options

    def show_option(self, option):
        '''
        return a list of options for the window

        todo: test and return True/False for on/off string

        :param option: option to return.
        :type option: string
        :rtype: string, int or bool
        '''

        window_option = self.tmux(
            'show-options', option
        ).stdout
        window_option = [tuple(item.split(' ')) for item in window_option][0]

        if window_option[1].isdigit():
            window_option = (window_option[0], int(window_option[1]))

        return window_option[1]

    def __repr__(self):
        return "%s(%s %s)" % (self.__class__.__name__, self.get('session_id'), self.get('session_name'))
