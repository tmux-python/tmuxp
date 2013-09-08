# -*- coding: utf8 - *-
"""
    tmuxp.server
    ~~~~~~~~~~~~

    tmuxp helps you manage tmux workspaces.

    :copyright: Copyright 2013 Tony Narlock.
    :license: BSD, see LICENSE for details
"""
from .util import live_tmux
from .session import Session
from .formats import SESSION_FORMATS
from .logxtreme import logging

try:
    from sh import tmux as tmux, ErrorReturnCode_1
except ImportError:
    logging.warning('tmux must be installed and in PATH\'s to use tmuxp')


class Server(object):
    '''
    ``t`` global. stores information on live, running tmux server

    :attr:`Server._sessions` [:class:`Session`, ..]
        :attr:`Session._windows` [:class:`Window`, ..]
            :attr:`Window._panes` [:class:`Pane`, ..]
                :class:`Pane`
    '''

    def __init__(self):
        self._sessions = list()

    def list_sessions(self):
        '''
        Return a list of :class:`Session` from tmux server.

        ``$ tmux list-sessions``
        '''
        formats = SESSION_FORMATS
        tmux_formats = ['#{%s}' % format for format in formats]

        sessions = tmux(
            'list-sessions',                    # ``tmux list-windows``
            '-F%s' % '\t'.join(tmux_formats),   # output
            _iter=True                          # iterate line by line
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

    def has_clients(self):
        # are any clients connected to tmux
        if len(tmux('list-clients')) > int(1):
            return True
        else:
            return False

    def attached_sessions(self):
        '''
            Returns active :class:`Session` object

            This will not work where multiple tmux sessions are attached.
        '''

        if not self._sessions:
            return None

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

    def has_session(self, session_name):
        '''
        ``$ tmux has-session``
        '''

        try:  # has-session returns nothing if session exists
            tmux('has-session', '-t', session_name)
            return True
        except ErrorReturnCode_1 as e:
            return False

    def kill_session(self, session_name=None):
        '''
        ``$ tmux kill-session``

        session_name
            string. note this accepts fnmatch(3).  'asdf' will kill asdfasd
        '''
        try:
            tmux('kill-session', '-t', session_name)
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

        target_session
            string. name of the session. fnmatch(3) works
        '''
        tmux('switch-client', '-t', target_session)
