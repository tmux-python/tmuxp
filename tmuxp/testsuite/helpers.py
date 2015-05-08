# -*- coding: utf-8 -*-
"""Helper methods for tmuxp unittests."""

from __future__ import absolute_import, division, print_function, \
    with_statement, unicode_literals

import time
import logging
import contextlib

try:
    import unittest2 as unittest
except ImportError:  # Python 2.7
    import unittest

from random import randint

from . import t
from .. import Server, log, exc

logger = logging.getLogger(__name__)

TEST_SESSION_PREFIX = 'test tmuxp_'


def get_test_session_name(server, prefix=TEST_SESSION_PREFIX):
    while True:
        session_name = prefix + str(randint(0, 9999999))
        if not t.has_session(session_name):
            break
    return session_name


def get_test_window_name(session, prefix=TEST_SESSION_PREFIX):
    while True:
        window_name = prefix + str(randint(0, 9999999))
        if not session.findWhere(window_name=window_name):
            break
    return window_name


@contextlib.contextmanager
def temp_session(server, session_name=None):
    if not session_name:
        session_name = get_test_session_name(server)

    session = server.new_session(session_name)
    try:
        yield session
    finally:
        if server.has_session(session_name):
            session.kill_session()
    return


@contextlib.contextmanager
def temp_session(server, *args, **kwargs):
    """Return a context manager with a temporary session.

    e.g.::

        with temp_session(server) as session:
            session.new_window(window_name='my window')

    The session will destroy itself upon closing with :meth:`Session.
    kill_session()`.

    If no ``session_name`` is entered, :func:`get_test_session_name` will make
    an unused session name.

    :args: Same arguments as :meth:`Server.new_session`
    :yields: Temporary session
    :rtype: :class:`Session`
    """

    if 'session_name' in kwargs:
        session_name = kwargs.pop('session_name')
    else:
        session_name = get_test_session_name(server)

    session = server.new_session(session_name, *args, **kwargs)

    try:
        yield session
    finally:
        if server.has_session(session_name):
            session.kill_session()
    return


@contextlib.contextmanager
def temp_window(session, *args, **kwargs):
    """Return a context manager with a temporary window.

    e.g.::

        with temp_window(session) as window:
            my_pane = window.split_window()

    The window will destroy itself upon closing with :meth:`window.
    kill_window()`.

    If no ``window_name`` is entered, :func:`get_test_window_name` will make
    an unused window name.

    :args: Same arguments as :meth:`Session.new_window`
    :yields: Temporary window
    :rtype: :class:`Window`
    """

    if 'window_name' not in kwargs:
        window_name = get_test_window_name(session)
    else:
        window_name = kwargs.pop('window_name')

    window = session.new_window(window_name, *args, **kwargs)

    # Get ``window_id`` before returning it, it may be killed within context.
    window_id = window.get('window_id')

    try:
        yield session
    finally:
        if session.findWhere(window_id=window_id):
            window.kill_window()
    return


class TestCase(unittest.TestCase):

    """Base TestClass so we don't have to try: unittest2 every module. """

    @classmethod
    def setUpClass(cls):
        super(TestCase, cls).setUpClass()  # for python 2.6 unittest2


class TmuxTestCase(TestCase):

    """TmuxTestCase class, wraps the TestCase in a :class:`Session`."""

    #: :class:`Session` object.
    session = None
    #: Session name for the TestCase.
    TEST_SESSION_NAME = None

    def temp_session(self, session_name=None):
        return temp_session(self.server, session_name)

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
            t.cmd('new-session', '-d', '-s', session_name)

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

        TEST_SESSION_NAME = get_test_session_name(server=t)

        try:
            session = t.new_session(
                session_name=TEST_SESSION_NAME,
            )
        except exc.TmuxpException as e:
            raise e

        """
        Make sure that tmuxp can :ref:`test_builder_visually` and switches to
        the newly created session for that testcase.
        """
        try:
            t.switch_client(session.get('session_id'))
            pass
        except exc.TmuxpException as e:
            # t.attach_session(session.get('session_id'))
            pass

        for old_test_session in old_test_sessions:
            logger.debug(
                'Old test test session %s found. Killing it.' %
                old_test_session
            )
            t.kill_session(old_test_session)
        assert TEST_SESSION_NAME == session.get('session_name')
        assert TEST_SESSION_NAME != 'tmuxp'

        self.TEST_SESSION_NAME = TEST_SESSION_NAME
        self.server = t
        self.session = session
