# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, with_statement

from .. import Pane, Window, Server
from .helpers import TmuxTestCase
from . import t

import logging

logger = logging.getLogger(__name__)


class SelectTest(TmuxTestCase):

    def test_select_window(self):
        window_count = len(self.session._windows)
        # to do, get option for   base-index from tmux
        # for now hoever, let's get the index from the first window.
        self.assertEqual(window_count, 1)

        window_base_index = int(
            self.session.attached_window().get('window_index'))

        window = self.session.new_window(window_name='testing 3')

        # self.assertEqual(2,
        # int(self.session.attached_window().get('window_index')))
        self.assertEqual(int(window_base_index) + 1, int(
            window.get('window_index')))

        self.session.select_window(window_base_index)
        self.assertEqual(window_base_index, int(
            self.session.attached_window().get('window_index')))

        self.session.select_window('testing 3')
        self.assertEqual(int(window_base_index) + 1, int(
            self.session.attached_window().get('window_index')))

        self.assertEqual(len(self.session._windows), 2)


class NewTest(TmuxTestCase):

    def test_zfresh_window_data(self):
        # self.session.select_window(1)
        #
        self.assertEqual(len(self.session.windows), 1)

        self.assertEqual(len(self.session.attached_window().panes), 1)
        current_windows = len(self.session._windows)
        self.assertNotEqual('@0', self.session.get('session_id'))
        self.assertEqual(current_windows, 1)

        self.assertEqual(len(self.session.attached_window().panes), 1)
        self.assertIsInstance(self.session.server, Server)
        # len(self.session.attached_window().panes))

        self.assertEqual(1, len(self.session.windows))
        self.assertEqual(len(self.session.attached_window().panes), 1)
        for w in self.session.windows:
            self.assertIsInstance(w, Window)
        window = self.session.attached_window()
        self.assertIsInstance(window, Window)
        self.assertEqual(len(self.session.attached_window().panes), 1)
        pane = window.split_window()
        self.session.attached_window().select_pane(0)
        self.session.attached_pane().send_keys('cd /srv/www/flaskr')
        self.session.attached_window().select_pane(1)
        self.session.attached_pane().send_keys('source .env/bin/activate')
        self.session.new_window(window_name='second')
        current_windows += 1
        self.assertEqual(current_windows, len(self.session._windows))
        self.session.new_window(window_name='hey')
        current_windows += 1
        self.assertEqual(current_windows, len(self.session._windows))

        self.session.select_window(1)
        self.session.kill_window(target_window='hey')
        current_windows -= 1
        self.assertEqual(current_windows, len(self.session._windows))


class NewTest2(TmuxTestCase):

    def test_newest_pane_data(self):
        # self.session.select_window(1)
        #
        #
        window = self.session.new_window(window_name='test', attach=True)
        self.assertIsInstance(window, Window)
        self.assertEqual(1, len(window.panes))
        window.split_window(attach=True)

        self.assertEqual(2, len(window.panes))
        # note: the below used to accept -h, removing because split_window now
        # has attach as its only argument now
        window.split_window(attach=True)
        self.assertEqual(3, len(window.panes))


class NewTest3(TmuxTestCase):

    def test_attached_pane(self):
        """Window.attached_window() returns active Pane"""

        window = self.session.attached_window()  # current window
        self.assertIsInstance(window.attached_pane(), Pane)


class NewTest4(TmuxTestCase):

    def test_split_window(self):
        """Window.split_window() splits window, returns new Pane."""
        window_name = 'test split window'
        window = self.session.new_window(window_name=window_name, attach=True)
        pane = window.split_window()
        self.assertEqual(2, len(window.panes))
        self.assertIsInstance(pane, Pane)


class RenameTest(TmuxTestCase):

    window_name_before = 'test'
    window_name_after = 'ha ha ha fjewlkjflwef'

    def test_window_rename(self):
        """Window.rename_window.rename_window()"""
        self.session.set_option('automatic-rename', 'off')
        window = self.session.new_window(
            window_name=self.window_name_before, attach=True)

        self.assertEqual(window, self.session.attached_window())
        self.assertEqual(window.get('window_name'), self.window_name_before)

        window.rename_window(self.window_name_after)

        window = self.session.attached_window()

        self.assertEqual(window.get('window_name'), self.window_name_after)

        window = self.session.attached_window()

        self.assertEqual(window.get('window_name'), self.window_name_after)


class RenameSpacesTest(RenameTest):
    window_name_after = 'hello \\ wazzup 0'


class KillWindow(TmuxTestCase):

    def test_kill_window(self):
        self.session.new_window()
        # create a second window to not kick out the client.
        # there is another way to do this via options too.

        w = self.session.attached_window()

        w.get('window_id')

        w.kill_window()
        with self.assertRaises(IndexError):
            w.get('window_id')


class Options(TmuxTestCase):

    def test_show_window_options(self):
        """Window.show_window_options() returns dict."""
        window = self.session.new_window(window_name='test_window')

        options = window.show_window_options()
        self.assertIsInstance(options, dict)

    def test_set_show_window_options(self):
        """Set option then Window.show_window_options(key)
        """
        window = self.session.new_window(window_name='test_window')

        window.set_window_option('main-pane-height', 20)
        self.assertEqual(20, window.show_window_options('main-pane-height'))

        window.set_window_option('main-pane-height', 40)
        self.assertEqual(40, window.show_window_options('main-pane-height'))

        self.assertEqual(40, window.show_window_options()['main-pane-height'])

    def test_show_window_option(self):
        """Set option then Window.show_window_option(key)
        """
        window = self.session.new_window(window_name='test_window')

        window.set_window_option('main-pane-height', 20)
        self.assertEqual(20, window.show_window_option('main-pane-height'))

        window.set_window_option('main-pane-height', 40)
        self.assertEqual(40, window.show_window_option('main-pane-height'))

        self.assertEqual(40, window.show_window_option('main-pane-height'))

    def test_set_window_option_bad(self):
        """Window.set_window_option raises ValueError for bad option key"""

        window = self.session.new_window(window_name='test_window')

        with self.assertRaises(ValueError):
            window.set_window_option('afewewfew', 43)
