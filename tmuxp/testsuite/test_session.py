# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, with_statement

from random import randint
from time import sleep
from .. import Session, Window, Pane
from ..util import tmux
from .helpers import TmuxTestCase, TEST_SESSION_PREFIX
from . import t

import logging

logger = logging.getLogger(__name__)


class SessionTest(TmuxTestCase):

    def test_has_session(self):
        """Server.has_session returns True if has session_name exists"""
        self.assertTrue(t.has_session(self.TEST_SESSION_NAME))
        self.assertFalse(t.has_session('asdf2314324321'))

    def test_select_window(self):
        """Session.select_window moves window"""
        # get the current window_base_index, since different user tmux config
        # may start at 0 or 1, or whatever they want.
        window_base_index = int(
            self.session.attached_window().get('window_index'))

        window = self.session.new_window(window_name='test_window')
        window_count = len(self.session._windows)

        self.assertGreaterEqual(window_count, 2)  # 2 or more windows

        self.assertEqual(len(self.session._windows), window_count)

        # tmux selects a window, moves to it, shows it as attached_window
        selected_window1 = self.session.select_window(window_base_index)
        self.assertIsInstance(selected_window1, Window)
        attached_window1 = self.session.attached_window()

        self.assertEqual(selected_window1, attached_window1)
        self.assertEqual(selected_window1.__dict__, attached_window1.__dict__)

        # again: tmux selects a window, moves to it, shows it as
        # attached_window
        selected_window2 = self.session.select_window(window_base_index + 1)
        self.assertIsInstance(selected_window2, Window)
        attached_window2 = self.session.attached_window()

        self.assertEqual(selected_window2, attached_window2)
        self.assertEqual(selected_window2.__dict__, attached_window2.__dict__)

        # assure these windows were really different
        self.assertNotEqual(selected_window1, selected_window2)
        self.assertNotEqual(
            selected_window1.__dict__, selected_window2.__dict__)

    def test_select_window_returns_Window(self):
        """Session.select_window returns Window object"""

        window_count = len(self.session._windows)
        self.assertEqual(len(self.session._windows), window_count)
        window_base_index = int(
            self.session.attached_window().get('window_index'))

        self.assertIsInstance(self.session.select_window(
            window_base_index), Window)

    def test_attached_window(self):
        """Session.attached_window() returns Window"""
        self.assertIsInstance(self.session.attached_window(), Window)

    def test_attached_pane(self):
        """Session.attached_pane() returns Pane"""
        self.assertIsInstance(self.session.attached_pane(), Pane)

    def test_session_rename(self):
        """Session.rename_session renames session"""
        test_name = 'testingdis_sessname'
        self.session.rename_session(test_name)
        self.assertEqual(self.session.get('session_name'), test_name)
        self.session.rename_session(self.TEST_SESSION_NAME)
        self.assertEqual(
            self.session.get('session_name'),
            self.TEST_SESSION_NAME
        )


class SessionNewTest(TmuxTestCase):

    def test_new_session(self):
        """Server.new_session creates new session"""
        new_session_name = TEST_SESSION_PREFIX + str(randint(0, 1337))
        new_session = t.new_session(session_name=new_session_name, detach=True)

        self.assertIsInstance(new_session, Session)
        self.assertEqual(new_session.get('session_name'), new_session_name)


class Options(TmuxTestCase):

    def test_show_options(self):
        """Session.show_options() returns dict."""

        options = self.session.show_options()
        self.assertIsInstance(options, dict)

    def test_set_show_options_single(self):
        """Set option then Session.show_options(key)
        """

        self.session.set_option('history-limit', 20)
        self.assertEqual(20, self.session.show_options('history-limit'))

        self.session.set_option('history-limit', 40)
        self.assertEqual(40, self.session.show_options('history-limit'))

        self.assertEqual(40, self.session.show_options()['history-limit'])

    def test_set_show_option(self):
        """Set option then Session.show_option(key)
        """
        self.session.set_option('history-limit', 20)
        self.assertEqual(20, self.session.show_option('history-limit'))

        self.session.set_option('history-limit', 40)

        self.assertEqual(40, self.session.show_option('history-limit'))

    def test_set_option_bad(self):
        """Session.set_option raises ValueError for bad option key"""
        with self.assertRaises(ValueError):
            self.session.set_option('afewewfew', 43)
