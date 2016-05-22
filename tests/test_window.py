# -*- coding: utf-8 -*-
"""Test for tmuxp Window object."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals, with_statement)

import logging
import pytest

from libtmux import Pane, Server, Window


logger = logging.getLogger(__name__)


def test_select_window(session):
    window_count = len(session._windows)
    # to do, get option for   base-index from tmux
    # for now hoever, let's get the index from the first window.
    assert window_count == 1

    window_base_index = int(
        session.attached_window().get('window_index'))

    window = session.new_window(window_name='testing 3')

    # self.assertEqual(2,
    # int(session.attached_window().get('window_index')))
    assert int(window_base_index) + 1 == int(window.get('window_index'))

    session.select_window(window_base_index)
    assert window_base_index == \
        int(session.attached_window().get('window_index'))

    session.select_window('testing 3')
    assert int(window_base_index) + 1 == \
        int(session.attached_window().get('window_index'))

    assert len(session._windows) == 2


def test_zfresh_window_data(session):
    pane_base_index = int(
        session.attached_window().show_window_option(
            'pane-base-index', g=True
        )
    )

    assert len(session.windows) == 1

    assert len(session.attached_window().panes) == 1
    current_windows = len(session._windows)
    assert session.get('session_id') != '@0'
    assert current_windows == 1

    assert len(session.attached_window().panes) == 1
    assert isinstance(session.server, Server)
    # len(session.attached_window().panes))

    assert len(session.windows), 1
    assert len(session.attached_window().panes) == 1
    for w in session.windows:
        assert isinstance(w, Window)
    window = session.attached_window()
    assert isinstance(window, Window)
    assert len(session.attached_window().panes) == 1
    window.split_window()
    session.attached_window().select_pane(pane_base_index)
    session.attached_pane().send_keys('cd /srv/www/flaskr')
    session.attached_window().select_pane(pane_base_index + 1)
    session.attached_pane().send_keys('source .venv/bin/activate')
    session.new_window(window_name='second')
    current_windows += 1
    assert current_windows == len(session._windows)
    session.new_window(window_name='hey')
    current_windows += 1
    assert current_windows == len(session._windows)

    session.select_window(1)
    session.kill_window(target_window='hey')
    current_windows -= 1
    assert current_windows == len(session._windows)


def test_newest_pane_data(session):
    window = session.new_window(window_name='test', attach=True)
    assert isinstance(window, Window)
    assert len(window.panes) == 1
    window.split_window(attach=True)

    assert len(window.panes) == 2
    # note: the below used to accept -h, removing because split_window now
    # has attach as its only argument now
    window.split_window(attach=True)
    assert len(window.panes) == 3


def test_attached_pane(session):
    """Window.attached_window() returns active Pane."""

    window = session.attached_window()  # current window
    assert isinstance(window.attached_pane(), Pane)


def test_split_window(session):
    """Window.split_window() splits window, returns new Pane."""
    window_name = 'test split window'
    window = session.new_window(window_name=window_name, attach=True)
    pane = window.split_window()
    assert len(window.panes) == 2
    assert isinstance(pane, Pane)


@pytest.mark.parametrize("window_name_before,window_name_after", [
    ('test', 'ha ha ha fjewlkjflwef'),
    ('test', 'hello \\ wazzup 0'),
])
def test_window_rename(session, window_name_before, window_name_after):
    """Window.rename_window()."""
    window_name_before = 'test'
    window_name_after = 'ha ha ha fjewlkjflwef'

    session.set_option('automatic-rename', 'off')
    window = session.new_window(
        window_name=window_name_before, attach=True)

    assert window == session.attached_window()
    assert window.get('window_name') == window_name_before

    window.rename_window(window_name_after)

    window = session.attached_window()

    assert window.get('window_name') == window_name_after

    window = session.attached_window()

    assert window.get('window_name') == window_name_after


def test_kill_window(session):
    session.new_window()
    # create a second window to not kick out the client.
    # there is another way to do this via options too.

    w = session.attached_window()

    w.get('window_id')

    w.kill_window()
    with pytest.raises(IndexError):
        w.get('window_id')


def test_show_window_options(session):
    """Window.show_window_options() returns dict."""
    window = session.new_window(window_name='test_window')

    options = window.show_window_options()
    assert isinstance(options, dict)


def test_set_show_window_options(session):
    """Set option then Window.show_window_options(key)."""
    window = session.new_window(window_name='test_window')

    window.set_window_option('main-pane-height', 20)
    assert window.show_window_options('main-pane-height') == 20

    window.set_window_option('main-pane-height', 40)
    assert window.show_window_options('main-pane-height') == 40
    assert window.show_window_options()['main-pane-height'] == 40


def test_show_window_option(session):
    """Set option then Window.show_window_option(key)."""
    window = session.new_window(window_name='test_window')

    window.set_window_option('main-pane-height', 20)
    assert window.show_window_option('main-pane-height') == 20

    window.set_window_option('main-pane-height', 40)
    assert window.show_window_option('main-pane-height') == 40
    assert window.show_window_option('main-pane-height') == 40


def test_set_window_option_bad(session):
    """Window.set_window_option raises ValueError for bad option key."""

    window = session.new_window(window_name='test_window')

    with pytest.raises(ValueError):
        window.set_window_option('afewewfew', 43)
