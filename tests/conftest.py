# -*- coding: utf-8 -*-

import logging

import pytest

from libtmux import exc
from libtmux.server import Server
from libtmux.test import TEST_SESSION_PREFIX, get_test_session_name, namer

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def server(request):
    t = Server()
    t.socket_name = 'tmuxp_test%s' % next(namer)

    def fin():
        t.kill_server()

    request.addfinalizer(fin)

    return t


@pytest.fixture(scope='function')
def session(server):
    session_name = 'tmuxp'

    if not server.has_session(session_name):
        server.cmd('new-session', '-d', '-s', session_name)

    # find current sessions prefixed with tmuxp
    old_test_sessions = [
        s.get('session_name')
        for s in server._sessions
        if s.get('session_name').startswith(TEST_SESSION_PREFIX)
    ]

    TEST_SESSION_NAME = get_test_session_name(server=server)

    try:
        session = server.new_session(session_name=TEST_SESSION_NAME)
    except exc.LibTmuxException as e:
        raise e

    """
    Make sure that tmuxp can :ref:`test_builder_visually` and switches to
    the newly created session for that testcase.
    """
    try:
        server.switch_client(session.get('session_id'))
        pass
    except exc.LibTmuxException:
        # server.attach_session(session.get('session_id'))
        pass

    for old_test_session in old_test_sessions:
        logger.debug('Old test test session %s found. Killing it.' % old_test_session)
        server.kill_session(old_test_session)
    assert TEST_SESSION_NAME == session.get('session_name')
    assert TEST_SESSION_NAME != 'tmuxp'

    return session


@pytest.fixture()
def tmpdir(tmpdir_factory):
    fn = tmpdir_factory.mktemp('tmuxp')
    return fn
