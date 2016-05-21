# -*- coding: utf-8 -*-
"""Test for tmuxp Session object."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals, with_statement)

import logging
import pytest

from tmuxp import Pane, Session, Window
from .helpers import TEST_SESSION_PREFIX, TmuxTestCase, namer

logger = logging.getLogger(__name__)


class SessionTest(TmuxTestCase):

    def test_has_session(self):
        """Server.has_session returns True if has session_name exists."""
        assert self.t.has_session(self.TEST_SESSION_NAME)
        assert not self.t.has_session('asdf2314324321')

    def test_select_window(self):
        """Session.select_window moves window."""
        # get the current window_base_index, since different user tmux config
        # may start at 0 or 1, or whatever they want.
        window_base_index = int(
            self.session.attached_window().get('window_index')
        )

        self.session.new_window(window_name='test_window')
        window_count = len(self.session._windows)

        assert window_count >= 2  # 2 or more windows

        assert len(self.session._windows) == window_count

        # tmux selects a window, moves to it, shows it as attached_window
        selected_window1 = self.session.select_window(window_base_index)
        assert isinstance(selected_window1, Window)
        attached_window1 = self.session.attached_window()

        assert selected_window1 == attached_window1
        assert selected_window1.__dict__ == attached_window1.__dict__

        # again: tmux selects a window, moves to it, shows it as
        # attached_window
        selected_window2 = self.session.select_window(window_base_index + 1)
        assert isinstance(selected_window2, Window)
        attached_window2 = self.session.attached_window()

        assert selected_window2 == attached_window2
        assert selected_window2.__dict__ == attached_window2.__dict__

        # assure these windows were really different
        assert selected_window1 != selected_window2
        assert selected_window1.__dict__ != selected_window2.__dict__

    def test_select_window_returns_Window(self):
        """Session.select_window returns Window object."""

        window_count = len(self.session._windows)
        assert len(self.session._windows) == window_count
        window_base_index = int(
            self.session.attached_window().get('window_index'))

        assert isinstance(
            self.session.select_window(window_base_index), Window
        )

    def test_attached_window(self):
        """Session.attached_window() returns Window."""
        assert isinstance(self.session.attached_window(), Window)

    def test_attached_pane(self):
        """Session.attached_pane() returns Pane."""
        assert isinstance(self.session.attached_pane(), Pane)

    def test_session_rename(self):
        """Session.rename_session renames session."""
        test_name = 'testingdis_sessname'
        self.session.rename_session(test_name)
        assert self.session.get('session_name') == test_name
        self.session.rename_session(self.TEST_SESSION_NAME)
        assert self.session.get('session_name') == self.TEST_SESSION_NAME


class SessionNewTest(TmuxTestCase):

    def test_new_session(self):
        """Server.new_session creates new session."""
        new_session_name = TEST_SESSION_PREFIX + next(namer)
        new_session = self.t.new_session(
            session_name=new_session_name, detach=True)

        assert isinstance(new_session, Session)
        assert new_session.get('session_name') == new_session_name


class Options(TmuxTestCase):

    def test_show_options(self):
        """Session.show_options() returns dict."""

        options = self.session.show_options()
        assert isinstance(options, dict)

    def test_set_show_options_single(self):
        """Set option then Session.show_options(key)."""

        self.session.set_option('history-limit', 20)
        assert self.session.show_options('history-limit') == 20

        self.session.set_option('history-limit', 40)
        assert self.session.show_options('history-limit') == 40

        assert self.session.show_options()['history-limit'] == 40

    def test_set_show_option(self):
        """Set option then Session.show_option(key)."""
        self.session.set_option('history-limit', 20)
        assert self.session.show_option('history-limit') == 20

        self.session.set_option('history-limit', 40)

        assert self.session.show_option('history-limit') == 40

    def test_set_option_bad(self):
        """Session.set_option raises ValueError for bad option key."""
        with pytest.raises(ValueError):
            self.session.set_option('afewewfew', 43)


class Environment(TmuxTestCase):

    def test_show_environment(self):
        """Session.show_environment() returns dict."""

        _vars = self.session.show_environment()
        assert isinstance(_vars, dict)

    def test_set_show_environment_single(self):
        """Set environment then Session.show_environment(key)."""

        self.session.set_environment('FOO', 'BAR')
        assert self.session.show_environment('FOO') == 'BAR'

        self.session.set_environment('FOO', 'DAR')
        assert self.session.show_environment('FOO') == 'DAR'

        assert self.session.show_environment()['FOO'] == 'DAR'

    def test_show_environment_not_set(self):
        """Not set environment variable returns None."""
        assert self.session.show_environment('BAR') is None

    def test_remove_environment(self):
        """Remove environment variable."""
        assert self.session.show_environment('BAM') is None
        self.session.set_environment('BAM', 'OK')
        assert self.session.show_environment('BAM') == 'OK'
        self.session.remove_environment('BAM')
        assert self.session.show_environment('BAM') is None

    def test_unset_environment(self):
        """Unset environment variable."""
        assert self.session.show_environment('BAM') is None
        self.session.set_environment('BAM', 'OK')
        assert self.session.show_environment('BAM') == 'OK'
        self.session.unset_environment('BAM')
        assert self.session.show_environment('BAM') is None
