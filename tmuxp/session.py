# -*- coding: utf8 - *-
"""
    tmuxp.session
    ~~~~~~~~~~~~~

    tmuxp helps you manage tmux workspaces.

    :copyright: Copyright 2013 Tony Narlock.
    :license: BSD, see LICENSE for details
"""
import pipes
from .util import TmuxObject, tmux
from .window import Window
from .formats import WINDOW_FORMATS, SESSION_FORMATS
from .exc import TmuxSessionExists
from .logxtreme import logging


class Session(TmuxObject):
    '''
    ``tmux(1) session``.

    Holds :class:`Window` objects.

    '''

    def __init__(self, **kwargs):
        self.session_name = None
        self._windows = list()

        # do we need this?
        if 'session_name' not in kwargs:
            raise ValueError('Session requires session_name')
        else:
            self.session_name = kwargs.get('session_name')

        self._TMUX = {}
        self.update(**kwargs)

    def rename_session(self, new_name):
        '''rename session and return new :class:`Session` object

        :param rename_session: new session name
        :type rename_session: string
        '''
        new_name = pipes.quote(new_name)
        try:
            tmux(
                'rename-session',
                '-t', pipes.quote(self.get('session_name')),
                new_name
            )
            self['session_name'] = new_name
        except:
            pass

        return self

    def new_window(self, window_name=None, automatic_rename=False):
        '''
        ``$ tmux new-window``

        :param window_name: window name::

            $ tmux new-window -n <window_name>
        :type window_name: string

        :param automatic_rename: assume automatic_rename if no window_name.
        :type automatic_rename: bool
        '''
        formats = ['session_name', 'session_id'] + WINDOW_FORMATS
        tmux_formats = ['#{%s}' % format for format in formats]

        if window_name:
            window = tmux(
                'new-window',
                '-P', '-F%s' % '\t'.join(tmux_formats),  # output
                '-n', window_name
            )
        else:
            window = tmux(
                'new-window',
                '-P', '-F%s' % '\t'.join(tmux_formats),  # output
            )

        window = dict(zip(formats, window.split('\t')))

        # clear up empty dict
        window = dict((k, v) for k, v in window.iteritems() if v)
        window = Window.from_tmux(session=self, **window)

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

        #if '-a' in args:
        #    tmux_args.append('-a')

        if target_window:
            tmux_args.append(['-t', target_window])

        tmux('kill-window', *tmux_args)

        self.list_windows()

    @classmethod
    def from_tmux(cls, **kwargs):
        '''
        Freeze of the current tmux session directly from the server. Returns
        :class:`Session`. Accepts a :class:`dict` of properties for a session.

        '''
        if 'session_name' not in kwargs:
            raise ValueError('Session requires session_name')

        session = cls(session_name=kwargs['session_name'])
        session.update(**kwargs)

        session._windows = session.list_windows()

        return session

    def _list_windows(self):
        '''
        Return dict of ``tmux(1) list-windows`` values.
        '''

        formats = ['session_name', 'session_id'] + WINDOW_FORMATS
        tmux_formats = ['#{%s}' % format for format in formats]

        windows = tmux(
            'list-windows',                     # ``tmux list-windows``
            '-t%s' % self.session_name,    # target (session name)
            '-F%s' % '\t'.join(tmux_formats),   # output
            _iter=True                          # iterate line by line
        )

        # combine format keys with values returned from ``tmux list-windows``
        windows = [dict(zip(formats, window.split('\t'))) for window in windows]

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
                logging.debug('adding window_name %s window_id %s' % (window['window_name'], window['window_id']))
                self._windows.append(Window.from_tmux(session=self, **window))
        else:
            new = {window['window_id']: window for window in new_windows}
            old = {window.get('window_id'): window for window in self._windows}

            created = set(new.keys()) - set(old.keys())
            deleted = set(old.keys()) - set(new.keys())
            intersect = set(new.keys()).intersection(set(old.keys()))

            diff = {id: dict(set(new[id].items()) - set(old[id].items())) for id in intersect}

            logging.info(
                "syncing windows"
                "\n\tdiff: %s\n"
                "\tcreated: %s\n"
                "\tdeleted: %s\n"
                "\tintersect: %s" % (diff, created, deleted, intersect)
            )

            for w in self._windows:
                # remove window objects if deleted or out of session
                if w.get('window_id') in deleted or self.get('session_id') != w.get('session_id'):
                    logging.debug("removing %s" % w)
                    self._windows.remove(w)

                if w.get('window_id') in intersect:
                    logging.debug('updating %s %s' % (w.get('window_name'), w.get('window_id')))
                    w.update(diff[w.get('window_id')])

            # create window objects for non-existant window_id's
            for window in [new[window_id] for window_id in created]:
                logging.debug('adding window_name %s window_id %s' % (window['window_name'], window['window_id']))
                self._windows.append(Window.from_tmux(session=self, **window))

        return self._windows

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
        tmux('select-window', '-t', target_window)
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
            logging.info('%s not clean, multiple windows', self)
            return False

        self.attached_window().list_panes()  # get the newest pane data

        if (len(self.attached_window()._panes) > 1):
            logging.info('%s not clean, multiple panes (%s)' % (self, len(self.attached_window()._panes)))
            return False

        if (int(self.attached_window().attached_pane().get('history_size')) > 0):
            logging.info('%s history_size (%s), greater than 0' % (self, self.attached_window().attached_pane().get('history_size')))
            return False

        return True

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.session_name)
