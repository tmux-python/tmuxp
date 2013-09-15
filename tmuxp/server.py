# -*- coding: utf8 - *-
"""
    tmuxp.server
    ~~~~~~~~~~~~

    tmuxp helps you manage tmux workspaces.

    :copyright: Copyright 2013 Tony Narlock.
    :license: BSD, see LICENSE for details
"""
import os
from .util import tmux
from .session import Session
from .formats import SESSION_FORMATS, CLIENT_FORMATS
from .logxtreme import logging
from .exc import TmuxNotRunning, TmuxSessionExists


class Server(object):

    '''
    The :term:`tmux(1)` server. Container for:

    :attr:`Server._sessions` [:class:`Session`, ..]
        :attr:`Session._windows` [:class:`Window`, ..]
            :attr:`Window._panes` [:class:`Pane`, ..]
                :class:`Pane`

    When instantiated, provides the``t`` global. stores information on live,
    running tmux server.
    '''

    socket_name = None
    socket_path = None
    config_file = None

    def __init__(self):
        self._sessions = list()

    def tmux(self, *args, **kwargs):
        args = list(args)
        if self.socket_name:
            args.insert(0, '-L{}'.format(self.socket_name))
        if self.socket_path:
            args.insert(0, '-S{}'.format(self.socket_path))
        if self.config_file:
            args.insert(0, '-f{}'.format(self.config_file))
        return tmux(*args, **kwargs)

    def hotswap(self, session_name=None):
        args = ['/usr/local/bin/tmux', 'tmux']
        if self.socket_name:
            args.append('-L{}'.format(self.socket_name))
        if self.socket_path:
            args.append('-S{}'.format(self.socket_path))
        if self.config_file:
            args.append('-f{}'.format(self.config_file))
        args.append('attach-session')
        if session_name:
            args.append('-t{}'.format(session_name))

        #logging.info(args)
        os.execl(*args)
        #os.execl('/usr/local/bin/tmux', 'tmux', 'attach-session', '-t', session_name)

    def list_sessions(self):
        '''
        Return a list of :class:`Session` from tmux server.

        ``$ tmux list-sessions``
        '''
        formats = SESSION_FORMATS
        tmux_formats = ['#{%s}' % format for format in formats]
        sessions = self.tmux(
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
                new_session = Session(server=self, **session)
                self._sessions.append(new_session)
            return self._sessions

        new = {session['session_id']: session for session in new_sessions}
        old = {session.get('session_id'): session for session in self._sessions}

        created = set(new.keys()) - set(old.keys()) or ()
        deleted = set(old.keys()) - set(new.keys()) or ()
        intersect = set(new.keys()).intersection(set(old.keys()))

        diff = {id: dict(set(new[id].items()) - set(old[id].items())) for id in intersect}

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
            logging.info(log_diff)

        for s in self._sessions:
            # remove session objects if deleted or out of session
            if s.get('session_id') in deleted:
                logging.info("removing %s" % s)
                self._sessions.remove(s)

            if s.get('session_id') in intersect and s.get('session_id') in diff:
                logging.debug('updating session_id %s session_name %s' % (s.get('session_id'), s.get('session_name')))
                s.update(diff[s.get('session_id')])

        # create session objects for non-existant session_id's
        for session in [new[session_id] for session_id in created]:
            logging.debug('new session %s' % session['session_id'])
            new_session = Session(server=self, **session)
            self._sessions.append(new_session)

        return self._sessions

    def list_clients(self):
        '''
        Return a list of :class:`client` from tmux server.

        ``$ tmux list-clients``
        '''
        formats = CLIENT_FORMATS
        tmux_formats = ['#{%s}' % format for format in formats]
        #import ipdb
        #ipdb.set_trace()
        clients = self.tmux(
            'list-clients',
            '-F%s' % '\t'.join(tmux_formats),   # output
            _iter=False                          # iterate line by line
        )

        # combine format keys with values returned from ``tmux list-windows``
        clients = [dict(zip(formats, client.split('\t'))) for client in clients]

        # clear up empty dict
        new_clients = [
            dict((k, v) for k, v in client.iteritems() if v) for client in clients
        ]

        if not self._clients:
            for client in new_clients:
                logging.debug('adding client_tty %s' % (client['client_tty']))
                self._clients.append(client)
            return self._clients

        new = {client['client_tty']: client for client in new_clients}
        old = {client.get('client_tty'): client for client in self._clients}

        created = set(new.keys()) - set(old.keys())
        deleted = set(old.keys()) - set(new.keys())
        intersect = set(new.keys()).intersection(set(old.keys()))

        diff = {id: dict(set(new[id].items()) - set(old[id].items())) for id in intersect}

        logging.info(
            "syncing clients"
            "\n\tdiff: %s\n"
            "\tcreated: %s\n"
            "\tdeleted: %s\n"
            "\tintersect: %s" % (diff, created, deleted, intersect)
        )

        for s in self._clients:
            # remove client objects if deleted or out of client
            if s.get('client_tty') in deleted:
                logging.info("removing %s" % s)
                self._clients.remove(s)

            if s.get('client_tty') in intersect:
                logging.debug('updating client_tty %s' % (s.get('client_tty')))
                s.update(diff[s.get('client_tty')])

        # create client objects for non-existant client_tty's
        for client in [new[client_tty] for client_tty in created]:
            logging.debug('new client %s' % client['client_tty'])
            self._clients.append(client)

        return self._clients

    def server_exists(self):
        '''server is on and exists

        '''

        try:
            self.tmux('list-clients')
            self.tmux('list-sessions')
            return True
        except TmuxNotRunning:
            return False

    def has_clients(self):
        # are any clients connected to tmux
        if len(self.tmux('list-clients')) > int(1):
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
                    logging.info('session %s attached', session.get('session_name'))
                    attached_sessions.append(session)
                else:
                    continue

        return attached_sessions or None

    def has_session(self, target_session):
        '''
        ``$ tmux has-session``

        :param: target_session: str of session name.

        returns True if session exists.
        '''

        try:  # has-session returns nothing if session exists
            if 'session not found' in self.tmux('has-session', '-t', target_session).stderr:
                return False
            else:
                return True
        except Exception as e:
            return False

    def kill_server(self):
        '''
        ``$ tmux kill-server``
        '''
        self.tmux('kill-server')

    def kill_session(self, target_session=None):
        '''
        ``$ tmux kill-session``

        :param: target_session: str. note this accepts fnmatch(3). 'asdf' will
                                kill asdfasd
        '''
        self.tmux('kill-session', '-t', target_session)
        self.list_sessions()

    @property
    def sessions(self):
        return self._sessions

    def switch_client(self, target_session):
        '''
        ``$ tmux switch-client``

        :param: target_session: str. name of the session. fnmatch(3) works.
        '''
        #tmux('switch-client', '-t', target_session)
        self.tmux('switch-client', '-t%s' %target_session)

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
                self.tmux('kill-session', '-t', session_name)
                logging.error('session %s exists. killed it.' % session_name)
            else:
                raise TmuxSessionExists('Session named %s exists' % session_name)

        logging.debug('creating session %s' % session_name)

        formats = SESSION_FORMATS
        tmux_formats = ['#{%s}' % format for format in formats]

        env = os.environ.get('TMUX')

        if env:
            del os.environ['TMUX']

        session_info = self.tmux(
            'new-session',
            '-d',  # assume detach = True for now, todo: fix
            '-s', session_name,
            '-P', '-F%s' % '\t'.join(tmux_formats),   # output
        )

        if env:
            os.environ['TMUX'] = env

        # combine format keys with values returned from ``tmux list-windows``
        session_info = dict(zip(formats, session_info.split('\t')))

        # clear up empty dict
        session_info = dict((k, v) for k, v in session_info.iteritems() if v)

        session = Session(server=self, **session_info)

        # need to be able to get first windows
        session._windows = session.list_windows()

        self._sessions.append(session)

        return session
