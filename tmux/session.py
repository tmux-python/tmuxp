# -*- coding: utf8 - *-
"""
    tmuxwrapper.session
    ~~~~~~~~~~~~~~~~~~~

    tmuxwrapper helps you manage tmux workspaces.

    :copyright: Copyright 2013 Tony Narlock <tony@git-pull.com>.
    :license: BSD, see LICENSE for details
"""
from .util import live_tmux, TmuxObject
from .window import Window
from .formats import WINDOW_FORMATS, SESSION_FORMATS
from .exc import SessionExists
from sh import tmux, ErrorReturnCode_1
from logxtreme import logging
import pipes


class Session(TmuxObject):
    '''
    tmux session

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
        '''rename session and return new Session object'''
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

    @classmethod
    def new_session(cls,
                    session_name=None,
                    kill_session=False,
                    *args,
                    **kwargs):
        '''
        ``tmux(1)`` ``new-session``

        Returns :class:`Session`

        Uses ``-P`` flag to print session info, ``-F`` for return formatting
        returns new Session object.

        ``tmux new-session -d`` will create the session in the background
        ``tmux new-session -Ad`` will move to the session name if it already
        exists. todo: make an option to handle this.

        session_name
            string. session name

            >>> tmux new-session -s <session_name>

        detach
            bool. create the new_session in the background, this is the same as

            >>> tmux new-session -d

        attach_if_exists
            bool. if the session_name exists, attach it. if False, this method
            will raise a SessionExists exception

        kill_session
            Kill current session if ``tmux has-session`` Useful for testing
            workspaces.
        '''

        ### ToDo: Update below to work with attach_if_exists
        try:
            # test this, returning NoneType
            if not len(tmux('has-session', '-t', session_name)):
                if kill_session:
                    tmux('kill-session', '-t', session_name)
                    logging.error('session %s exists. killed it.' % session_name)
                else:
                    raise SessionExists('Session named %s exists' % session_name)
        except ErrorReturnCode_1:
            pass

        logging.debug('creating session %s' % session_name)

        formats = SESSION_FORMATS
        tmux_formats = ['#{%s}' % format for format in formats]

        session_info = tmux(
            'new-session',
            '-d',  # assume detach = True for now, todo: fix
            '-s', session_name,
            '-P', '-F%s' % '\t'.join(tmux_formats),   # output
            *args
        )

        # combine format keys with values returned from ``tmux list-windows``
        session_info = dict(zip(formats, session_info.split('\t')))

        # clear up empty dict
        session_info = dict((k, v) for k, v in session_info.iteritems() if v)

        session = cls(session_name=session_name)
        session.update(session_info)

        # need to be able to get first windows
        session._windows = session.list_windows()

        return session

    @live_tmux
    def new_window(self, window_name=None, automatic_rename=False):
        '''
        tmux(1) new-window

        window_name
            string. window name (-n)

        automatic_rename
            bool. assume automatic_rename if no window_name
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

    @live_tmux
    def kill_window(self, target_window=None):
        '''
        tmux(1) kill-window

        Kill the current window or the window at ``target-window``. removing it
        from any sessions to which it is linked.
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
        :class:`Session`

        session_name
            name of the tmux session

        '''
        if 'session_name' not in kwargs:
            raise ValueError('Session requires session_name')

        session = cls(session_name=kwargs['session_name'])
        session.update(**kwargs)

        session._windows = session.list_windows()

        return session

    @live_tmux
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

    @live_tmux
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
            Returns active :class:`Window` object
        '''

        for window in self.list_windows():
            if 'window_active' in window:
                # for now window_active is a unicode
                if window.get('window_active') == '1':
                    return window
                else:
                    continue

        return False

    def select_window(self, window):
        '''
            ``tmux(1) select-window``

            window
                integer of the window index, also can be 'last-window' (-l),
                'next-window' (-n), or 'previous-window' (-p).
        '''
        tmux('select-window', '-t', window)
        self.list_windows()
        return self.attached_window()

    def attached_pane(self):
        '''
            Returns active :class:`Pane` object
        '''
        return self.attached_window().attached_pane()

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.session_name)
