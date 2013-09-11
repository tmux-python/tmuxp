# -*- coding: utf8 - *-
"""
    tmuxp.server
    ~~~~~~~~~~~~

    tmuxp helps you manage tmux workspaces.

    :copyright: Copyright 2013 Tony Narlock.
    :license: BSD, see LICENSE for details
"""
from .util import tmux
from .session import Session
from .formats import SESSION_FORMATS
from .logxtreme import logging
from .exc import TmuxNotRunning, TmuxSessionExists


class Server(object):
    '''
    The ``tmux(1)`` server. Container for:

    :attr:`Server._sessions` [:class:`Session`, ..]
        :attr:`Session._windows` [:class:`Window`, ..]
            :attr:`Window._panes` [:class:`Pane`, ..]
                :class:`Pane`

    When instantiated, provides the``t`` global. stores information on live,
    running tmux server.
    '''

    client = None

    def __init__(self):
        self._sessions = list()

    def list_sessions(self):
        '''
        Return a list of :class:`Session` from tmux server.

        ``$ tmux list-sessions``
        '''
        formats = SESSION_FORMATS
        tmux_formats = ['#{%s}' % format for format in formats]
        #import ipdb
        #ipdb.set_trace()
        sessions = tmux(
            'list-sessions',
            '-F%s' % '\t'.join(tmux_formats),   # output
            _iter=False                          # iterate line by line
        )

        # combine format keys with values returned from ``tmux list-windows``
        sessions = [dict(zip(formats, session.split('\t'))) for session in sessions]

        # clear up empty dict
        new_sessions = [
            dict((k, v) for k, v in session.iteritems() if v) for session in sessions
        ]

        if not self._sessions:
            for session in new_sessions:
                logging.debug('adding session_id %s' % (session['session_id']))
                self._sessions.append(Session.from_tmux(**session))
            return self._sessions

        new = {session['session_id']: session for session in new_sessions}
        old = {session.get('session_id'): session for session in self._sessions}

        created = set(new.keys()) - set(old.keys())
        deleted = set(old.keys()) - set(new.keys())
        intersect = set(new.keys()).intersection(set(old.keys()))

        diff = {id: dict(set(new[id].items()) - set(old[id].items())) for id in intersect}

        logging.info(
            "syncing sessions"
            "\n\tdiff: %s\n"
            "\tcreated: %s\n"
            "\tdeleted: %s\n"
            "\tintersect: %s" % (diff, created, deleted, intersect)
        )

        for s in self._sessions:
            # remove session objects if deleted or out of session
            if s.get('session_id') in deleted:
                logging.info("removing %s" % s)
                self._sessions.remove(s)

            if s.get('session_id') in intersect:
                logging.debug('updating session_id %s' % (s.get('session_id')))
                s.update(diff[s.get('session_id')])

        # create session objects for non-existant session_id's
        for session in [new[session_id] for session_id in created]:
            logging.debug('new session %s' % session['session_id'])
            self._sessions.append(Session.from_tmux(**session))

        return self._sessions

    def server_exists(self):
        '''server is on and exists

        '''

        try:
            tmux('list-clients')
            tmux('list-sessions')
            return True
        except TmuxNotRunning:
            return False

    def has_clients(self):
        # are any clients connected to tmux
        if len(tmux('list-clients')) > int(1):
            return True
        else:
            return False
        #if e.stderr == 'failed to connect to server':
        #    raise TmuxNotRunning('tmux session not running. please start'
        #                            'a tmux session in another terminal '
        #                            'window and continue.')

    def attached_sessions(self):
        '''
            Returns active :class:`Session` object

            This will not work where multiple tmux sessions are attached.
        '''

        sessions = self._sessions
        attached_sessions = list()

        for session in sessions:
            if 'session_attached' in session:
                # for now session_active is a unicode
                if session.get('session_attached') == '1':
                    logging.info('session %s attached', session.session_name)
                    attached_sessions.append(session)
                else:
                    continue

        return attached_sessions or None

    @staticmethod
    def has_session(target_session):
        '''
        ``$ tmux has-session``

        :param: target_session: str of session name.

        returns True if session exists.
        '''

        try:  # has-session returns nothing if session exists
            if 'session not found' in tmux('has-session', '-t', target_session).stderr:
                return False
            else:
                return True
        except Exception as e:
            logging.error('160 %s' % e)
            return False

    def kill_session(self, target_session=None):
        '''
        ``$ tmux kill-session``

        :param: target_session: str. note this accepts fnmatch(3). 'asdf' will
                                kill asdfasd
        '''
        try:
            tmux('kill-session', '-t', target_session)
            self.list_sessions()
        except ErrorReturnCode_1 as e:
            logging.debug(
                "\n\tcmd:\t%s\n"
                "\terror:\t%s"
                % (e.full_cmd, e.stderr)
            )
            return False

    @property
    def sessions(self):
        return self._sessions

    def switch_client(self, target_session):
        '''
        ``$ tmux switch-client``

        :param: target_session: str. name of the session. fnmatch(3) works.
        '''
        tmux('switch-client', '-t', target_session)

    def new_session(self,
                    session_name=None,
                    kill_session=False,
                    *args,
                    **kwargs):
        '''
        ``$ tmux new-session``

        Returns :class:`Session`

        Uses ``-P`` flag to print session info, ``-F`` for return formatting
        returns new Session object.

        ``$ tmux new-session -d`` will create the session in the background
        ``$ tmux new-session -Ad`` will move to the session name if it already
        exists. todo: make an option to handle this.

        :param session_name: session name::

            $ tmux new-session -s <session_name>
        :type session_name: string

        :param detach: create session background::

            $ tmux new-session -d
        :type detach: bool

        :param attach_if_exists: if the session_name exists, attach it.
                                 if False, this method will raise a
                                 :exc:`tmuxp.exc.TmuxSessionExists` exception
        :type attach_if_exists: bool

        :param kill_session: Kill current session if ``$ tmux has-session``
                             Useful for testing workspaces.
        :type kill_session: bool
        '''

        ### ToDo: Update below to work with attach_if_exists
        if self.has_session(session_name):
            if kill_session:
                tmux('kill-session', '-t', session_name)
                logging.error('session %s exists. killed it.' % session_name)
            else:
                raise TmuxSessionExists('Session named %s exists' % session_name)

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

        session = Session(session_name=session_name)
        session.update(session_info)

        # need to be able to get first windows
        session._windows = session.list_windows()

        self.list_sessions()  # get fresh data for sessions on Server object

        return session
