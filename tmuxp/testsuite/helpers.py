# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, with_statement

import time
from random import randint

try:
    import unittest2 as unittest
except ImportError:  # Python 2.7
    import unittest
from . import t
from .. import Server, log, exc
import logging
logger = logging.getLogger(__name__)

TEST_SESSION_PREFIX = 'tmuxp_'


class TestCase(unittest.TestCase):

    """Base TestClass so we don't have to try: unittest2 every module. """


class TmuxTestCase(TestCase):

    """TmuxTestCase class, wraps the TestCase in a :class:`Session`."""

    #: :class:`Session` object.
    session = None
    #: Session name for the TestCase.
    TEST_SESSION_NAME = None

    def setUp(self):
        """Run bootstrap if :attr:`~.session` is not set."""
        if not self.TEST_SESSION_NAME or not self.session:
            self.bootstrap()

    def bootstrap(self):
        """Return tuple of the session_name (generated) and :class:`Session`.

        Checks to verify if the user has a tmux client open.

        It will clean up and delete other sessions starting with the
        :attr:`TEST_SESSION_PREFIX` ``tmuxp``.

        Since tmux closes when all sessions are deleted, the bootstrap will see
        if there is no other client open aside from a tmuxp_ prefixed session
        a dumby session will be made to prevent tmux from closing.

        """

        session_name = 'tmuxp'
        if not t.has_session(session_name):
            t.tmux('new-session', '-d', '-s', session_name)

        # find current sessions prefixed with tmuxp
        old_test_sessions = [
            s.get('session_name') for s in t._sessions
            if s.get('session_name').startswith(TEST_SESSION_PREFIX)
        ]

        other_sessions = [
            s.get('session_name') for s in t._sessions
            if not s.get('session_name').startswith(
                TEST_SESSION_PREFIX
            )
        ]

        # assert session_list == t.sessions

        TEST_SESSION_NAME = TEST_SESSION_PREFIX + str(randint(0, 13370))
        try:
            session = t.new_session(
                session_name=TEST_SESSION_NAME,
            )
        except exc.TmuxpException as e:
            raise e

        '''
        Make sure that tmuxp can :ref:`test_builder_visually` and switches to the
        newly created session for that testcase.
        '''
        try:
            t.switch_client(session.get('session_id'))
            pass
        except exc.TmuxpException as e:
            #t.attach_session(session.get('session_id'))
            pass

        for old_test_session in old_test_sessions:
            logger.debug('Old test test session %s found. Killing it.' %
                        old_test_session)
            t.kill_session(old_test_session)
        assert TEST_SESSION_NAME == session.get('session_name')
        assert TEST_SESSION_NAME != 'tmuxp'

        self.TEST_SESSION_NAME = TEST_SESSION_NAME
        self.session = session
