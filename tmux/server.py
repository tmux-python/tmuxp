# -*- coding: utf8 - *-
"""
    tmuxwrapper.server
    ~~~~~~~~~~~~~~~~~~

    tmuxwrapper helps you manage tmux workspaces.

    :copyright: Copyright 2013 Tony Narlock <tony@git-pull.com>.
    :license: BSD, see LICENSE for details
"""
from util import live_tmux
from .session import Session
from sh import tmux, ErrorReturnCode_1
from .formats import SESSION_FORMATS
from logxtreme import logging


class Server(object):
    '''
    ``t`` global. stores information on live, running tmux server

    Server.sessions [<Session>, ..]
        Session.windows [<Window>, ..]
            Window.panes [<Pane>, ..]
                Pane

    Panes, Windows and Sessions which are populated with _TMUX MetaData.

    This is an experimental design choice to just leave `-F` commands to give
    _TMUX information, decorate methods to throw an exception if it requires
    interaction with tmux

    With :attrib:`._TMUX` :class:`Session` and :class:`Window` can be accessed
    as a property, and the session and window may be looked up dynamically.

    The children inside a ``t`` object are created live. We should look into
    giving them context managers so::

        with Server.select_session(fnmatch):
            # have access to session object
            # note at this level fnmatch may have to be done via python
            # and list-sessions to retrieve object correctly
            session.la()
            with session.attached_window() as window:
                # access to current window
                pass
            with session.find_window(fnmatch) as window:
                # access to tmux matches window
                with window.attached_path() as pane:
                    # access to pane
                    pass

    '''

    def __init__(self):
        self._sessions = list()

    def list_sessions(self):
        '''
        Return a list of :class:`Session` from tmux server.

        ``tmux(1)`` ``list-sessions``
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
        sessions = [
            dict((k, v) for k, v in session.iteritems() if v) for session in sessions
        ]

        #sessions = [Session.from_tmux(**session) for session in sessions]

        new_sessions = sessions

        if not self._sessions:
            for session in new_sessions:
                logging.debug('adding session_id %s' % (session['session_id']))
                self._sessions.append(Session.from_tmux(**session))
            return self._sessions

        new = {session['session_id']: session for session in new_sessions}
        old = {session._TMUX['session_id']: session for session in self._sessions}
        print old
        print old.keys()

        created = set(new.keys()) - set(old.keys())
        deleted = set(old.keys()) - set(new.keys())
        intersect = set(new.keys()).intersection(set(old.keys()))

        diff = {id: dict(set(new[id].items()) - set(old[id]._TMUX.items())) for id in intersect}

        logging.info(
            "syncing sessions"
            "\n\tdiff: %s\n"
            "\tcreated: %s\n"
            "\tdeleted: %s\n"
            "\tintersect: %s" % (diff, created, deleted, intersect)
        )

        for s in self._sessions:
            # remove session objects if deleted or out of session
            if s._TMUX['session_id'] in deleted:
                logging.info("removing %s" % s)
                self._sessions.remove(s)

            if s._TMUX['session_id'] in intersect:
                logging.debug('updating session_id %s' % (s._TMUX['session_id']))
                s._TMUX.update(diff[s._TMUX['session_id']])

        # create session objects for non-existant session_id's
        for session in [new[session_id] for session_id in created]:
            logging.debug('new session %s' % session['session_id'])
            self._sessions.append(Session.from_tmux(**session))

        #self._sessions = [session.from_tmux(session=self._session, window=self, **session) for session in sessions]

        return self._sessions

    def has_clients(self):
        # are any clients connected to tmux
        if len(tmux('list-clients')) > 1:
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
            if 'session_attached' in session._TMUX:
                # for now session_active is a unicode
                if session._TMUX['session_attached'] == '1':
                    logging.info('session %s attached', session.session_name)
                    attached_sessions.append(session)
                else:
                    continue

        return attached_sessions or None

    def has_session(self, session_name):
        '''
        ``tmux(1)`` ``has-session``
        '''

        # has-session returns nothing if session exists
        try:
            tmux('has-session', '-t', session_name)
            return True
        except ErrorReturnCode_1 as e:
            return False

    def kill_session(self, session_name=None):
        '''
        ``tmux(1)`` ``kill-session``

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

    def list_clients(self):
        raise NotImplemented

    def switch_client(self, target_session):
        '''
        ``tmux(1) ``switch-client``

        target_session
            string. name of the session. fnmatch(3) works
        '''
        tmux('switch-client', '-t', target_session)
