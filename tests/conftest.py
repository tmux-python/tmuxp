# -*- coding: utf-8 -*-

import pytest

import logging
from tmuxp import exc
from tmuxp.server import Server

from .helpers import get_test_session_name, TEST_SESSION_PREFIX

logger = logging.getLogger(__name__)


@pytest.fixture(scope='session')
def t():
    t = Server()
    t.socket_name = 'tmuxp_test'

    return t


@pytest.fixture(scope='function')
def session(t):
    session_name = 'tmuxp'
    if not t.has_session(session_name):
        t.cmd('new-session', '-d', '-s', session_name)

    # find current sessions prefixed with tmuxp
    old_test_sessions = [
        s.get('session_name') for s in t._sessions
        if s.get('session_name').startswith(TEST_SESSION_PREFIX)
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

    return session


@pytest.fixture()
def tmpdir(tmpdir_factory):
    fn = tmpdir_factory.mktemp('tmuxp')
    return fn
