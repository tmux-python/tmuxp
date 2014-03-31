# -*- coding: utf-8 -*-
"""Tests for tmuxp testsuite's helper and utility functions."""

from __future__ import absolute_import, division, print_function, \
    with_statement, unicode_literals

from .helpers import get_test_session_name, temp_session, TestCase, \
    TmuxTestCase, unittest  # , temp_window, temp_pane


class TempSession(TmuxTestCase):

    def test_kills_session(self):
        server = self.server
        session_name = get_test_session_name(server=server)

        with temp_session(server=server, session_name=session_name) as session:
            result = server.has_session(session_name)
            self.assertTrue(result)

        self.assertFalse(server.has_session(session_name))

    def test_if_session_killed_before(self):
        """Handles situation where session already closed within context"""

        server = self.server
        session_name = get_test_session_name(server=server)

        with temp_session(server=server, session_name=session_name) as session:

            # an error or an exception within a temp_session kills the session
            server.kill_session(session_name)

            result = server.has_session(session_name)
            self.assertFalse(result)

        # really dead?
        self.assertFalse(server.has_session(session_name))

    def test_if_session_name_works(self):
        """should allow custom ``session_name``."""
        pass


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TempSession))
    return suite
