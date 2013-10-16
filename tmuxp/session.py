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
from .formats import WINDOW_FORMATS, SESSION_FORMATS
from .exc import TmuxSessionExists

from . import log, util
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

        self._windows = list()
        self.children = self._windows
        self._TMUX = {}
        self.update(**kwargs)

        self.list_windows()

    def tmux(self, *args, **kwargs):
        # if '-t' not in kwargs:
        #    kwargs['-t'] = self.get['session_id']
        return self.server.tmux(*args, **kwargs)

    def refresh(self):
        '''Refresh current :class:`Session` object. Chainable.

        :rtype: :class:`Session`
        '''
        self._TMUX = self.server.getById(self['session_id'])._TMUX

        return self

    def rename_session(self, new_name):
        '''rename session and return new :class:`Session` object

        :param rename_session: new session name
        :type rename_session: string
        '''
        new_name = pipes.quote(new_name)
        try:
            self.tmux(
                'rename-session',
                '-t%s' % self.get('session_id'),
                new_name
            )
            self['session_name'] = new_name
        except:
            pass

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
        formats = ['session_name', 'session_id'] + WINDOW_FORMATS
        tmux_formats = ['#{%s}' % format for format in formats]

        window_args = (
            '-t%s' % self.get('session_id'),
            '-P',
            '-F%s' % '\t'.join(tmux_formats),  # output
        )

        if window_name:
            window_args += ('-n', window_name)

        if not attach:
            window_args += ('-d',)

        window = self.tmux('new-window', *window_args)

        window = window.stdout[0]

        window = dict(zip(formats, window.split('\t')))

        # clear up empty dict
        window = dict((k, v) for k, v in window.iteritems() if v)
        window = Window(session=self, **window)
        window.list_panes()

        if automatic_rename:
            window.set_window_option('automatic-rename', True)

        self._windows.append(window)

        self.list_windows()
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

        self.tmux('kill-window', target)

        self.list_windows()

    def _list_windows(self):
        '''
        Return dict of ``tmux(1) list-windows`` values.
        '''

        formats = ['session_name', 'session_id'] + WINDOW_FORMATS
        tmux_formats = ['#{%s}' % format for format in formats]

        windows = self.tmux(
            'list-windows',                     # ``tmux list-windows``
            '-t%s' % self.get('session_id'),    # target (session name)
            '-F%s' % '\t'.join(tmux_formats),   # output
        ).stdout

        # combine format keys with values returned from ``tmux list-windows``
        windows = [dict(zip(
            formats, window.split('\t'))) for window in windows]

        # clear up empty dict
        windows = [
            dict((k, v) for k, v in window.iteritems() if v) for window in windows
        ]

        return windows

    def list_windows(self):
        '''
        Return a list of :class:`Window` from the ``tmux(1)`` session.
        '''
        new_windows = self._list_windows()

        if not self._windows:
            for window in new_windows:
                logger.debug('adding window_name %s window_id %s' % (
                    window['window_name'], window['window_id']))
                self._windows.append(Window(session=self, **window))
        else:
            new = {window.get('window_id'): window for window in new_windows}
            old = {window.get('window_id'): window for window in self._windows}

            created = set(new.keys()) - set(old.keys()) or ()
            deleted = set(old.keys()) - set(new.keys()) or ()
            intersect = set(new.keys()).intersection(set(old.keys()))

            diff = {id: dict(set(new[id].items()) - set(
                old[id].items())) for id in intersect}

            intersect = set(k for k, v in diff.iteritems() if v) or ()
            diff = dict((k, v) for k, v in diff.iteritems() if v) or ()

            if diff or created or deleted:
                log_diff = "sync sessions for server:\n"
            else:
                log_diff = None
            if diff and intersect:
                log_diff += "diff %s for %s" % (diff, intersect)
            if created:
                log_diff += "created %s" % created
            if deleted:
                log_diff += "deleted %s" % deleted
            if log_diff:
                logger.debug(log_diff)

            for w in self._windows:
                # remove window objects if deleted or out of session
                if w.get('window_id') in deleted or self.get('session_id') != w.get('session_id'):
                    logger.debug("removing %s" % w)
                    self._windows.remove(w)

                if w.get('window_id') in intersect and w.get('window_id') in diff:
                    logger.debug('updating %s %s' % (
                        w.get('window_name'), w.get('window_id'))
                    )
                    w.update(diff[w.get('window_id')])

            # create window objects for non-existant window_id's
            for window in [new[window_id] for window_id in created]:
                logger.debug('adding window_name %s window_id %s' % (
                    window['window_name'], window['window_id']))
                self._windows.append(Window(session=self, **window))

        return self._windows
    list_children = list_windows

    def attached_window(self):
        '''
            Returns active :class:`Window` object.
        '''

        for window in self.list_windows():
            if 'window_active' in window:
                # for now window_active is a unicode
                if window.get('window_active') == '1':
                    return window
                else:
                    continue

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

        self.tmux('select-window', target)

        self.list_windows()
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
            logger.info('%s not clean, multiple windows', self)
            return False

        self.attached_window().list_panes()  # get the newest pane data

        if (len(self.attached_window()._panes) > 1):
            logger.info('%s not clean, multiple panes (%s)' % (
                self, len(self.attached_window()._panes)))
            return False

        if (int(self.attached_window().attached_pane().get('history_size')) > 0):
            logger.info('%s history_size (%s), greater than 0' % (
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

        for key, value in session_options.iteritems():
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
