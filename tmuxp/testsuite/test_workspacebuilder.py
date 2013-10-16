# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, with_statement

import os
import unittest
import logging
import kaptan
from .. import Window, config, exc
from ..workspacebuilder import WorkspaceBuilder
from .helpers import TmuxTestCase

logger = logging.getLogger(__name__)


class TwoPaneTest(TmuxTestCase):

    yaml_config = '''
    session_name: sampleconfig
    start_directory: '~'
    windows:
    - layout: main-vertical
      panes:
      - shell_command:
        - vim
        start_directory: '~'
      - shell_command:
        - cowsay "hey"
      window_name: editor
    - panes:
      - shell_command:
        - tail -F /var/log/syslog
        start_directory: /var/log
      window_name: logging
    - window_name: test
      automatic_rename: true
      panes:
      - shell_command:
        - htop
    '''

    def test_split_windows(self):
        s = self.session
        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(self.yaml_config).get()

        builder = WorkspaceBuilder(sconf=sconfig)

        window_count = len(self.session._windows)  # current window count
        self.assertEqual(len(s.list_windows()), window_count)
        for w, wconf in builder.iter_create_windows(s):
            window_pane_count = len(w._panes)
            for p in builder.iter_create_panes(w, wconf):
                p = p
                self.assertEqual(len(s.list_windows()), window_count)
            self.assertIsInstance(w, Window)

            self.assertEqual(len(s.list_windows()), window_count)
            window_count += 1


class ThreePaneTest(TmuxTestCase):

    yaml_config = '''
    session_name: sampleconfig
    start_directory: '~'
    windows:
    - window_name: test
      layout: main-horizontal
      panes:
      - shell_command:
        - vim
        start_directory: '~'
      - shell_command:
        - cowsay "hey"
      - shell_command:
        - cowsay "moo"
    '''

    def test_split_windows(self):
        s = self.session
        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(self.yaml_config).get()

        builder = WorkspaceBuilder(sconf=sconfig)

        window_count = len(self.session._windows)  # current window count
        self.assertEqual(len(s.list_windows()), window_count)
        for w, wconf in builder.iter_create_windows(s):

            window_pane_count = len(w._panes)
            for p in builder.iter_create_panes(w, wconf):
                p = p
                self.assertEqual(len(s.list_windows()), window_count)
            self.assertIsInstance(w, Window)

            self.assertEqual(len(s.list_windows()), window_count)
            window_count += 1
            w.set_window_option('main-pane-height', 50)
            w.select_layout(wconf['layout'])


class FocusTest(TmuxTestCase):

    yaml_config = '''
    session_name: sampleconfig
    start_directory: '~'
    windows:
    - window_name: focused window
      layout: main-horizontal
      focus: true
      panes:
      - shell_command:
        - vim
        start_directory: '~'
      - shell_command:
        - cowsay "hey"
      - shell_command:
        - cowsay "moo"
        - top
        focus: true
    - window_name: window 2
      panes:
      - shell_command:
        - vim
        start_directory: '~'
        focus: true
      - shell_command:
        - cowsay "hey"
      - shell_command:
        - cowsay "moo"

    '''

    @unittest.skip(
        'attached_{pane,window} needs to be fixed, this is working on tmux'
        ' 1.9, if focus: true isn\'t working for you, please file an issue.'
    )
    def test_split_windows(self):
        s = self.session
        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(self.yaml_config).get()
        import sys

        builder = WorkspaceBuilder(sconf=sconfig)

        builder.build(session=self.session)

        self.assertEqual(
            self.session.attached_window().get('window_name'),
           'focused window'
        )

        pane_base_index = self.session.attached_window().show_window_option('base-pane-index')

        if not pane_base_index:
            pane_base_index = 0
        else:
            pane_base_index = int(pane_base_index)


        # logger.error('attached window: %s' % (self.session.attached_window()))
        # logger.error('attached window: %s' % (self.session.attached_window()._TMUX))
        # logger.error('attached pane: %s' % (self.session.attached_window().attached_pane()))
        import time
        time.sleep(1)
        self.session.list_windows()
        self.session.attached_window().list_panes()
        logger.error('attached pane: %s' % (self.session.attached_window().attached_pane().refresh()))
        logger.error('attached pane: %s' % (self.session.attached_window().attached_pane())._TMUX)
        logger.error('attached pane: %s' % (self.session.attached_window().list_panes()))
        logger.error('attached pane: %s' % (self.session.attached_window().where({'pane_active': '1'})[0]._TMUX))



        for pane in self.session.attached_window().list_panes():
            logger.error(
                '%s and %s and %s, total panes %s' %
                (pane, pane['pane_index'], pane.window.get('window_name'), len(self.session.attached_window().list_panes()))
            )

        self.assertEqual(
            self.session.attached_window().attached_pane().get('pane_index'),
            pane_base_index + 2
        )



class WindowOptions(TmuxTestCase):
    '''sample config with no session name'''

    yaml_config = '''
    session_name: test window options
    start_directory: '~'
    windows:
    - layout: main-horizontal
      options:
        main-pane-height: 30
      panes:
      - shell_command:
        - vim
        start_directory: '~'
      - shell_command:
        - cowsay "hey"
      - shell_command:
        - cowsay "moo"
      window_name: editor
    '''

    def test_window_options(self):
        s = self.session
        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(self.yaml_config).get()

        builder = WorkspaceBuilder(sconf=sconfig)

        window_count = len(self.session._windows)  # current window count
        self.assertEqual(len(s.list_windows()), window_count)
        for w, wconf in builder.iter_create_windows(s):

            window_pane_count = len(w._panes)
            for p in builder.iter_create_panes(w, wconf):
                p = p
                self.assertEqual(len(s.list_windows()), window_count)
            self.assertIsInstance(w, Window)
            self.assertEqual(w.show_window_option('main-pane-height'), 30)

            self.assertEqual(len(s.list_windows()), window_count)
            window_count += 1
            w.select_layout(wconf['layout'])


class TestsToDo(object):

    def test_uses_first_window_if_exists(self):
        '''
        if the session is already on the first window, use that.

        this is useful if the user is already inside of a tmux session
        '''

    def test_same_session_already_exists_unclean(self):
        '''
        raise exception if session_name already exists and has multiple
        windows the user could potentially be offered to add a cli argument to
        override the session_name in config. Perhaps `-n` could be used to load
        a config from file with overridden session_name.
        '''

    def test_inside_tmux_same_session_already_exists(self):
        ''' same as above, but when the config file and the current $TMUX
        session are the same '''

    def test_inside_tmux_no_session_name_exists(self):
        '''
        if the session_name doesn't currently exist and the user is in tmux
        rename the current session by the config / -n and build there.
        '''

    def testPaneProportions(self):
        """
        todo. checking the proportions of a pane on a grid allows
        us to verify a window has been build correctly without
        needing to see the tmux session itself.

        we expect panes in a list to be ordered and show up to
        their corresponding pane_index.
        """
        pass


if __name__ == '__main__':
    #t.socket_name = 'tmuxp_test'
    unittest.main()
