# -*- coding: utf-8 -*-
import logging
import os

import pytest

from libtmux import exc
from libtmux.server import Server
from libtmux.test import TEST_SESSION_PREFIX, get_test_session_name, namer

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def monkeypatch_plugin_test_packages(monkeypatch):
    paths = [
        "tests/fixtures/pluginsystem/plugins/tmuxp_test_plugin_bwb/",
        "tests/fixtures/pluginsystem/plugins/tmuxp_test_plugin_bs/",
        "tests/fixtures/pluginsystem/plugins/tmuxp_test_plugin_r/",
        "tests/fixtures/pluginsystem/plugins/tmuxp_test_plugin_owc/",
        "tests/fixtures/pluginsystem/plugins/tmuxp_test_plugin_awf/",
        "tests/fixtures/pluginsystem/plugins/tmuxp_test_plugin_fail/",
    ]
    for path in paths:
        monkeypatch.syspath_prepend(os.path.abspath(os.path.relpath(path)))


@pytest.fixture(scope='function')
def socket_name(request):
    return 'tmuxp_test%s' % next(namer)


@pytest.fixture(scope='function')
def server(request, socket_name):
    t = Server()
    t.socket_name = socket_name

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
