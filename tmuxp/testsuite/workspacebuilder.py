# -*- coding: utf-8 -*-
"""Test for tmuxp workspacebuilder.

tmuxp.tests.workspacebuilder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

from __future__ import absolute_import, division, print_function, \
    with_statement, unicode_literals

import os
import sys
import logging
import unittest
import subprocess
import time

import kaptan

from .. import Window, config, exc
from .._compat import text_type
from ..workspacebuilder import WorkspaceBuilder
from .helpers import TestCase, TmuxTestCase, temp_session

logger = logging.getLogger(__name__)

current_dir = os.path.abspath(os.path.dirname(__file__))
example_dir = os.path.abspath(os.path.join(current_dir, '..', '..', 'examples'))
fixtures_dir = os.path.abspath(os.path.join(current_dir, 'fixtures'))


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
        - tail | echo 'hi'
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
        - cd ~
      - shell_command:
        - cd /usr
        focus: true
      - shell_command:
        - cd ~
        - echo "moo"
        - top
    - window_name: window 2
      panes:
      - shell_command:
        - top
        focus: true
      - shell_command:
        - echo "hey"
      - shell_command:
        - echo "moo"
    - window_name: window 3
      panes:
      - shell_command: cd /
        focus: true
      - pane
      - pane
    """

    def test_focus_pane_index(self):
        s = self.session
        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(self.yaml_config).get()
        sconfig = config.expand(sconfig)
        sconfig = config.trickle(sconfig)

        builder = WorkspaceBuilder(sconf=sconfig)

        builder.build(session=self.session)

        self.assertEqual(
            self.session.attached_window().get('window_name'),
            'focused window'
        )

        pane_base_index = int(self.session.attached_window().show_window_option(
            'pane-base-index', g=True
        ))

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

        w = self.session.attached_window()

        self.assertNotEqual(w.get('window_name'), 'man')

        pane_path = '/usr'
        for i in range(60):
            p = w.attached_pane()
            p.server._update_panes()
            if p.get('pane_current_path') == pane_path:
                break
            time.sleep(.2)

        self.assertEqual(p.get('pane_current_path'), pane_path)

        proc = self.session.tmux('show-option', '-gv', 'base-index')
        base_index = int(proc.stdout[0])
        self.session.server._update_windows()

        window3 = self.session.findWhere({'window_index': str(base_index + 2)})
        self.assertIsInstance(window3, Window)

        p = None
        pane_path = '/'
        for i in range(60):
            p = window3.attached_pane()
            p.server._update_panes()
            if p.get('pane_current_path') == pane_path:
                break
            time.sleep(.2)

        self.assertEqual(p.get('pane_current_path'), pane_path)


class WindowOptions(TmuxTestCase):

    yaml_config = """
    session_name: test window options
    start_directory: '~'
    windows:
    - layout: main-horizontal
      options:
        main-pane-height: 5
      panes:
      - pane
      - pane
      - pane
      window_name: editor
    """

    def test_window_options(self):
        s = self.session
        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(self.yaml_config).get()
        sconfig = config.expand(sconfig)

        builder = WorkspaceBuilder(sconf=sconfig)

        window_count = len(self.session._windows)  # current window count
        self.assertEqual(len(s._windows), window_count)
        for w, wconf in builder.iter_create_windows(s):

            window_pane_count = len(w._panes)
            for p in builder.iter_create_panes(w, wconf):
                p = p
                self.assertEqual(len(s._windows), window_count)
            self.assertIsInstance(w, Window)
            self.assertEqual(w.show_window_option('main-pane-height'), 5)

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
        """With option automatic-rename: on."""
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

        for i in range(60):
            self.session.server._update_windows()
            if w.get('window_name') != 'man':
                break
            time.sleep(.1)

        self.assertNotEqual(w.get('window_name'), 'man')

        pane_base_index = w.show_window_option('pane-base-index', g=True)
        w.select_pane(pane_base_index)

        for i in range(60):
            self.session.server._update_windows()
            if w.get('window_name') == 'man':
                break
            time.sleep(.1)

        self.assertEqual(w.get('window_name'), text_type('man'))

        w.select_pane('-D')
        for i in range(60):
            self.session.server._update_windows()
            if w['window_name'] != 'man':
                break
            time.sleep(.1)

        self.assertNotEqual(w.get('window_name'), text_type('man'))


class BlankPaneTest(TmuxTestCase):

    """:todo: Verify blank panes of various types build into workspaces."""

    yaml_config_file = os.path.join(example_dir, 'blank-panes.yaml')

    def test_blank_pane_count(self):

        test_config = kaptan.Kaptan().import_config(self.yaml_config_file).get()
        test_config = config.expand(test_config)
        # for window in test_config['windows']:
        #     window['layout'] = 'tiled'
        builder = WorkspaceBuilder(sconf=test_config)
        builder.build(session=self.session)

        self.assertEqual(self.session, builder.session)

        window1 = self.session.findWhere({'window_name': 'Blank pane test'})
        self.assertEqual(len(window1._panes), 3)

        window2 = self.session.findWhere({'window_name': 'More blank panes'})
        self.assertEqual(len(window2._panes), 3)

        window3 = self.session.findWhere(
            {'window_name': 'Empty string (return)'}
        )
        self.assertEqual(len(window3._panes), 3)

        window4 = self.session.findWhere({'window_name': 'Blank with options'})
        self.assertEqual(len(window4._panes), 2)


class StartDirectoryTest(TmuxTestCase):
    yaml_config = """
    session_name: sampleconfig
    start_directory: '/usr'
    windows:
    - window_name: supposed to be /usr/bin
      start_directory: '/usr/bin'
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
    - window_name: cwd containing a space
      start_directory: /tmp/foo bar
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

    def setUp(self):
        super(StartDirectoryTest, self).setUp()
        if not os.path.exists('/tmp/foo bar'):
            os.mkdir('/tmp/foo bar')
            self._temp_dir_created = True
        else:
            self._temp_dir_created = False

    def tearDown(self):
        super(StartDirectoryTest, self).tearDown()
        if self._temp_dir_created:
            os.rmdir('/tmp/foo bar')

    def test_start_directory(self):

        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(self.yaml_config).get()
        sconfig = config.expand(sconfig)
        sconfig = config.trickle(sconfig)

        builder = WorkspaceBuilder(sconf=sconfig)
        builder.build(session=self.session)

        assert(self.session == builder.session)
        dirs = ['/usr/bin', '/dev', '/tmp/foo bar', '/usr', os.getcwd()]
        for path, window in zip(dirs, self.session.windows):
            for p in window.panes:
                for i in range(60):
                    p.server._update_panes()
                    if p.get('pane_current_path') == path:
                        break
                    time.sleep(.2)

                self.assertEqual(p.get('pane_current_path'), path)


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
      layout: tiled
      panes:
      - cd /usr/bin
      - cd /usr
      - cd /sbin
      - cd /home
    """

    def test_pane_order(self):

        # test order of `panes` (and pane_index) above aganist pane_dirs
        pane_paths = [
            '/usr/bin',
            '/usr',
            '/sbin',
            '/home'
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
            pane_base_index = w.show_window_option('pane-base-index', g=True)
            for p_index, p in enumerate(w.list_panes(), start=pane_base_index):
                self.assertEqual(int(p_index), int(p.get('pane_index')))

                # pane-base-index start at base-index, pane_paths always start
                # at 0 since python list.
                pane_path = pane_paths[p_index - pane_base_index]

                for i in range(60):
                    p.server._update_panes()
                    if p.get('pane_current_path') == pane_path:
                        break
                    time.sleep(.2)

                self.assertEqual(p.get('pane_current_path'), pane_path)


class WindowIndexTest(TmuxTestCase):
    yaml_config = """
    session_name: sampleconfig
    windows:
    - window_name: zero
      panes:
      - echo 'zero'
    - window_name: five
      panes:
      - echo 'five'
      window_index: 5
    - window_name: one
      panes:
      - echo 'one'
    """

    def test_window_index(self):
        proc = self.session.tmux('show-option', '-gv', 'base-index')
        base_index = int(proc.stdout[0])
        name_index_map = {
            'zero': 0 + base_index,
            'one': 1 + base_index,
            'five': 5,
        }

        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(self.yaml_config).get()
        sconfig = config.expand(sconfig)
        sconfig = config.trickle(sconfig)

        builder = WorkspaceBuilder(sconf=sconfig)

        for window, wconf in builder.iter_create_windows(self.session):
            expected_index = name_index_map[window['window_name']]
            self.assertEqual(int(window['window_index']), expected_index)


class BeforeLoadScript(TmuxTestCase):

    config_script_not_exists = """
    session_name: sampleconfig
    before_script: {fixtures_dir}/script_not_exists.sh
    windows:
    - panes:
      - pane
    """

    config_script_fails = """
    session_name: sampleconfig
    before_script: {fixtures_dir}/script_failed.sh
    windows:
    - panes:
      - pane
    """

    config_script_completes = """
    session_name: sampleconfig
    before_script: {fixtures_dir}/script_complete.sh
    windows:
    - panes:
      - pane
    """

    def test_throw_error_if_retcode_false(self):

        sconfig = kaptan.Kaptan(handler='yaml')
        yaml = self.config_script_fails.format(
            fixtures_dir=fixtures_dir
        )
        sconfig = sconfig.import_config(yaml).get()
        sconfig = config.expand(sconfig)
        sconfig = config.trickle(sconfig)

        builder = WorkspaceBuilder(sconf=sconfig)

        with self.temp_session() as sess:
            session_name = sess.get('session_name')

            with self.assertRaises(subprocess.CalledProcessError):
                builder.build(session=sess)

            result = self.server.has_session(session_name)
            self.assertFalse(
                result,
                msg="Kills session if before_script exits with errcode"
            )

    def test_throw_error_if_file_not_exists(self):

        sconfig = kaptan.Kaptan(handler='yaml')
        yaml = self.config_script_not_exists.format(
            fixtures_dir=fixtures_dir
        )
        sconfig = sconfig.import_config(yaml).get()
        sconfig = config.expand(sconfig)
        sconfig = config.trickle(sconfig)

        builder = WorkspaceBuilder(sconf=sconfig)

        with self.temp_session() as sess:
            session_name = sess.get('session_name')
            temp_session_exists = self.server.has_session(sess.get('session_name'))
            self.assertTrue(temp_session_exists)
            with self.assertRaisesRegexp(
                (BeforeLoadScriptNotExists, OSError),
                'No such file or directory'
            ):
                builder.build(session=sess)
            result = self.server.has_session(session_name)
            self.assertFalse(
                result,
                msg="Kills session if before_script doesn't exist"
            )

    def test_true_if_test_passes(self):

        sconfig = kaptan.Kaptan(handler='yaml')
        yaml = self.config_script_completes.format(
            fixtures_dir=fixtures_dir
        )
        sconfig = sconfig.import_config(yaml).get()
        sconfig = config.expand(sconfig)
        sconfig = config.trickle(sconfig)

        builder = WorkspaceBuilder(sconf=sconfig)

        with self.temp_session() as session:
            builder.build(session=self.session)


from ..workspacebuilder import run_before_script, BeforeLoadScriptNotExists, \
    BeforeLoadScriptFailed


class RunBeforeScript(TestCase):

    def test_raise_BeforeLoadScriptNotExists_if_not_exists(self):
        script_file = os.path.join(fixtures_dir, 'script_noexists.sh')

        with self.assertRaises(BeforeLoadScriptNotExists):
            run_before_script(script_file)

        with self.assertRaises(OSError):
            run_before_script(script_file)

    def test_raise_BeforeLoadScriptFailed_if_retcode(self):
        script_file = os.path.join(fixtures_dir, 'script_failed.sh')

        with self.assertRaises(BeforeLoadScriptFailed):
            run_before_script(script_file)

        with self.assertRaises(subprocess.CalledProcessError):
            run_before_script(script_file)

    def test_return_stdout_if_exits_zero(self):
        script_file = os.path.join(fixtures_dir, 'script_complete.sh')

        run_before_script(script_file)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BeforeLoadScript))
    suite.addTest(unittest.makeSuite(RunBeforeScript))
    suite.addTest(unittest.makeSuite(BlankPaneTest))
    suite.addTest(unittest.makeSuite(FocusAndPaneIndexTest))
    suite.addTest(unittest.makeSuite(PaneOrderingTest))
    suite.addTest(unittest.makeSuite(StartDirectoryTest))
    suite.addTest(unittest.makeSuite(ThreePaneTest))
    suite.addTest(unittest.makeSuite(TwoPaneTest))
    suite.addTest(unittest.makeSuite(WindowAutomaticRename))
    suite.addTest(unittest.makeSuite(WindowIndexTest))
    suite.addTest(unittest.makeSuite(WindowOptions))
    return suite
