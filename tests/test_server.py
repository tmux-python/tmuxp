# -*- coding: utf-8 -*-
"""Test for tmuxp Server object."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals, with_statement)

import logging

from libtmux import Server

logger = logging.getLogger(__name__)


def test_has_session(server, session):
    assert server.has_session(session.get('session_name'))
    assert not server.has_session('asdf2314324321')


def test_socket_name(server):
    """ ``-L`` socket_name.

    ``-L`` socket_name  file name of socket. which will be stored in
            env TMUX_TMPDIR or /tmp if unset.)

    """
    myserver = Server(socket_name='test')

    assert myserver.socket_name == 'test'


def test_socket_path(server):
    """ ``-S`` socket_path  (alternative path for server socket). """
    myserver = Server(socket_path='test')

    assert myserver.socket_path == 'test'


def test_config(server):
    """ ``-f`` file for tmux(1) configuration. """
    myserver = Server(config_file='test')
    assert myserver.config_file == 'test'


def test_256_colors(server):
    myserver = Server(colors=256)
    assert myserver.colors == 256

    proc = myserver.cmd('list-servers')

    assert '-2' in proc.cmd
    assert '-8' not in proc.cmd


def test_88_colors(server):
    myserver = Server(colors=88)
    assert myserver.colors == 88

    proc = myserver.cmd('list-servers')

    assert '-8' in proc.cmd
    assert '-2' not in proc.cmd


def test_show_environment(server):
    """Server.show_environment() returns dict."""
    _vars = server.show_environment()
    assert isinstance(_vars, dict)


def test_set_show_environment_single(server, session):
    """Set environment then Server.show_environment(key)."""
    server.set_environment('FOO', 'BAR')
    assert 'BAR' == server.show_environment('FOO')

    server.set_environment('FOO', 'DAR')
    assert 'DAR' == server.show_environment('FOO')

    assert 'DAR' == server.show_environment()['FOO']


def test_show_environment_not_set(server):
    """Unset environment variable returns None."""
    assert server.show_environment('BAR') is None
