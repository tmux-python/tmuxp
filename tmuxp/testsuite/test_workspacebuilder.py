# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, with_statement

import os
import sys
import logging
import time
import kaptan
from .. import Window, config, exc
from ..util import unicode
from ..workspacebuilder import WorkspaceBuilder
from .helpers import TmuxTestCase

logger = logging.getLogger(__name__)

current_dir = os.path.abspath(os.path.dirname(__file__))
example_dir = os.path.abspath(os.path.join(current_dir, '..', '..', 'examples'))


class TwoPaneTest(TmuxTestCase):

    yaml_config = """
    session_name: sampleconfig
    start_directory: '~'
    windows:
    - layout: main-vertical
      panes:
      - shell_command:
        - vim
      - shell_command:
        - echo "hey"
      window_name: editor
    - panes:
      - shell_command:
        - tail -F /var/log/syslog
      window_name: logging
    - window_name: test
      panes:
      - shell_command:
        - htop
    """

    def test_split_windows(self):
        s = self.session
        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(self.yaml_config).get()

        builder = WorkspaceBuilder(sconf=sconfig)

        window_count = len(self.session._windows)  # current window count
        self.assertEqual(len(s._windows), window_count)
        for w, wconf in builder.iter_create_windows(s):
            window_pane_count = len(w._panes)
            for p in builder.iter_create_panes(w, wconf):
                p = p
                self.assertEqual(len(s._windows), window_count)
            self.assertIsInstance(w, Window)

            self.assertEqual(len(s._windows), window_count)
            window_count += 1


class ThreePaneTest(TmuxTestCase):

    yaml_config = """
    session_name: sampleconfig
    start_directory: '~'
    windows:
    - window_name: test
      layout: main-horizontal
      panes:
      - shell_command:
        - vim
      - shell_command:
        - echo "hey"
      - shell_command:
        - echo "moo"
    """

    def test_split_windows(self):
        s = self.session
        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(self.yaml_config).get()

        builder = WorkspaceBuilder(sconf=sconfig)

        window_count = len(self.session._windows)  # current window count
        self.assertEqual(len(s._windows), window_count)
        for w, wconf in builder.iter_create_windows(s):

            window_pane_count = len(w._panes)
            for p in builder.iter_create_panes(w, wconf):
                p = p
                self.assertEqual(len(s._windows), window_count)
            self.assertIsInstance(w, Window)

            self.assertEqual(len(s._windows), window_count)
            window_count += 1
            w.set_window_option('main-pane-height', 50)
            w.select_layout(wconf['layout'])


class FocusAndPaneIndexTest(TmuxTestCase):

    yaml_config = """
    session_name: sampleconfig
    start_directory: '~'
    windows:
    - window_name: focused window
      layout: main-horizontal
      focus: true
      panes:
      - shell_command:
        - vim
      - shell_command:
        - echo "hey"
      - shell_command:
        - echo "moo"
        - top
        focus: true
    - window_name: window 2
      panes:
      - shell_command:
        - vim
        rocus: true
      - shell_command:
        - echo "hey"
      - shell_command:
        - echo "moo"

    """

    def test_split_windows(self):
        s = self.session
        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(self.yaml_config).get()

        builder = WorkspaceBuilder(sconf=sconfig)

        builder.build(session=self.session)

        self.assertEqual(
            self.session.attached_window().get('window_name'),
            'focused window'
        )

        pane_base_index = self.session.attached_window().show_window_option(
            'pane-base-index'
        )

        if not pane_base_index:
            pane_base_index = 0
        else:
            pane_base_index = int(pane_base_index)

        # get the pane index for each pane
        pane_base_indexes = []
        for pane in self.session.attached_window().panes:
            pane_base_indexes.append(int(pane.get('pane_index')))

        pane_indexes_should_be = [pane_base_index + x for x in range(0, 3)]
        self.assertListEqual(pane_indexes_should_be, pane_base_indexes)


class WindowOptions(TmuxTestCase):

    yaml_config = """
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
        - echo "hey"
      - shell_command:
        - echo "moo"
      window_name: editor
    """

    def test_window_options(self):
        s = self.session
        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(self.yaml_config).get()

        builder = WorkspaceBuilder(sconf=sconfig)

        window_count = len(self.session._windows)  # current window count
        self.assertEqual(len(s._windows), window_count)
        for w, wconf in builder.iter_create_windows(s):

            window_pane_count = len(w._panes)
            for p in builder.iter_create_panes(w, wconf):
                p = p
                self.assertEqual(len(s._windows), window_count)
            self.assertIsInstance(w, Window)
            self.assertEqual(w.show_window_option('main-pane-height'), 30)

            self.assertEqual(len(s._windows), window_count)
            window_count += 1
            w.select_layout(wconf['layout'])


class WindowAutomaticRename(TmuxTestCase):

    yaml_config = """
    session_name: test window options
    start_directory: '~'
    windows:
    - layout: main-horizontal
      options:
        automatic-rename: on
      panes:
      - shell_command:
        - man echo
        start_directory: '~'
      - shell_command:
        - echo "hey"
      - shell_command:
        - echo "moo"
    """

    def test_automatic_rename_option(self):
        """ with option automatic-rename: on. """
        s = self.session
        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(self.yaml_config).get()

        builder = WorkspaceBuilder(sconf=sconfig)

        window_count = len(self.session._windows)  # current window count
        self.assertEqual(len(s._windows), window_count)
        for w, wconf in builder.iter_create_windows(s):

            window_pane_count = len(w._panes)
            for p in builder.iter_create_panes(w, wconf):
                p = p
                self.assertEqual(len(s._windows), window_count)
            self.assertIsInstance(w, Window)
            self.assertEqual(w.show_window_option('automatic-rename'), 'on')

            self.assertEqual(len(s._windows), window_count)

            window_count += 1
            w.select_layout(wconf['layout'])

        self.assertNotEqual(s.get('session_name'), 'tmuxp')
        w = s.windows[0]

        for i in range(30):
            if w.get('window_name') != 'man':
                break
            time.sleep(.5)

        self.assertNotEqual(w.get('window_name'), 'man')

        pane_base_index = w.show_window_option('pane-base-index', g=True)
        w.select_pane(pane_base_index)

        for i in range(30):
            self.session.server._update_windows()
            if w.get('window_name') == 'man':
                break
            time.sleep(.5)

        self.assertEqual(w.get('window_name'), unicode('man'))

        w.select_pane('-D')
        for i in range(30):
            if w['window_name'] != 'man':
                break
            time.sleep(.5)

        self.assertEqual(w.get('window_name'), unicode('man'))


class BlankPaneTest(TmuxTestCase):

    """:todo: Verify blank panes of various types build into workspaces."""

    yaml_config_file = os.path.join(example_dir, 'blank-panes.yaml')

    def test_blank_pane_count(self):

        test_config = kaptan.Kaptan().import_config(self.yaml_config_file).get()
        test_config = config.expand(test_config)
        builder = WorkspaceBuilder(sconf=test_config)
        builder.build(session=self.session)

        window1 = self.session.findWhere({'window_name': 'Blank pane test'})
        self.assertEqual(len(window1._panes), 6)

        window1 = self.session.findWhere({'window_name': 'Empty string (return)'})
        self.assertEqual(len(window1._panes), 3)

        self.assertEqual(self.session, builder.session)


class StartDirectoryTest(TmuxTestCase):
    yaml_config = """
    session_name: sampleconfig
    start_directory: '/var'
    windows:
    - window_name: supposed to be /var/log
      start_directory: '/var/log'
      layout: main-horizontal
      options:
          main-pane-height: 50
      panes:
      - shell_command:
        - echo "hey"
      - shell_command:
        - echo "moo"
    - window_name: support to be /dev
      start_directory: '/dev'
      layout: main-horizontal
      panes:
      - shell_command:
        - pwd
      - shell_command:
        - echo "hey"
      - shell_command:
        - echo "moo"
    - window_name: testsa3
      layout: main-horizontal
      panes:
      - shell_command:
        - pwd
      - shell_command:
        - echo "hey"
      - shell_command:
        - echo "moo3"
    - window_name: cwd relative to config file
      layout: main-horizontal
      start_directory: ./
      panes:
      - shell_command:
        - pwd
      - shell_command:
        - echo "hey"
      - shell_command:
        - echo "moo3"
    """

    def test_start_directory(self):

        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(self.yaml_config).get()
        sconfig = config.expand(sconfig)
        sconfig = config.trickle(sconfig)

        builder = WorkspaceBuilder(sconf=sconfig)
        builder.build(session=self.session)

        assert(self.session == builder.session)
        for path in ['/var/log', '/dev/', '/var/', os.getcwd()]:
            for window in self.session.windows:
                for p in window.panes:
                    self.assertTrue(p.get('pane_start_path', path))


class PaneOrderingTest(TmuxTestCase):

    """Pane ordering based on position in config and ``pane_index``.

    Regression test for https://github.com/tony/tmuxp/issues/15.

    """

    yaml_config = """
    session_name: sampleconfig
    start_directory: '~'
    windows:
    - options:
      - automatic_rename: on
      panes:
      - cd /var/log
      - cd /sys
      - cd /sbin
      - cd /tmp
    """

    def test_pane_order(self):

        # test order of `panes` (and pane_index) above aganist pane_dirs
        pane_paths = [
            '/var/log',
            '/sys',
            '/sbin',
            '/tmp'
        ]
        s = self.session
        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(self.yaml_config).get()
        sconfig = config.expand(sconfig)
        sconfig = config.trickle(sconfig)

        builder = WorkspaceBuilder(sconf=sconfig)

        window_count = len(self.session._windows)  # current window count
        self.assertEqual(len(s._windows), window_count)
        for w, wconf in builder.iter_create_windows(s):
            window_pane_count = len(w._panes)
            for p in builder.iter_create_panes(w, wconf):
                p = p
                self.assertEqual(len(s._windows), window_count)

            self.assertIsInstance(w, Window)

            self.assertEqual(len(s._windows), window_count)
            window_count += 1

        for w in self.session.windows:
            import time
            time.sleep(1)
            pane_base_index = w.show_window_option('pane-base-index', g=True)
            for p_index, p in enumerate(w.list_panes(), start=pane_base_index):
                self.assertEqual(int(p_index), int(p.get('pane_index')))

                # pane-base-index start at base-index, pane_paths always start
                # at 0 since python list.
                pane_path = pane_paths[p_index - pane_base_index]

                for i in range(30):
                    p.server._update_panes()
                    if p.get('pane_current_path') == pane_path:
                        break
                    time.sleep(.5)

                self.assertEqual(p.get('pane_current_path'), pane_path)
