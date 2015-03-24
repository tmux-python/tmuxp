# -*- coding: utf-8 -*-
"""Test for tmuxp workspacebuilder.

tmuxp.tests.workspacebuilder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

from __future__ import absolute_import, division, print_function, \
    with_statement, unicode_literals

import os
import platform
import sys
import logging
import unittest
import tempfile
import time

import kaptan

from .. import Window, config, exc
from .._compat import text_type
from ..workspacebuilder import WorkspaceBuilder
from .helpers import TestCase, TmuxTestCase, temp_session

logger = logging.getLogger(__name__)

current_dir = os.path.realpath(os.path.dirname(__file__))
example_dir = os.path.realpath(os.path.join(current_dir, '..', '..', 'examples'))
fixtures_dir = os.path.realpath(os.path.join(current_dir, 'fixtures'))


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
        for i in range(10):
            p = w.attached_pane()
            p.server._update_panes()
            if p.get('pane_current_path') == pane_path:
                break
            time.sleep(.4)

        self.assertEqual(p.get('pane_current_path'), pane_path)

        proc = self.session.tmux('show-option', '-gv', 'base-index')
        base_index = int(proc.stdout[0])
        self.session.server._update_windows()

        window3 = self.session.findWhere({'window_index': str(base_index + 2)})
        self.assertIsInstance(window3, Window)

        p = None
        pane_path = '/'
        for i in range(10):
            p = window3.attached_pane()
            p.server._update_panes()
            if p.get('pane_current_path') == pane_path:
                break
            time.sleep(.4)

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

        man_window_name = 'man'

        # BSD operating systems will wrap manual pages in less
        if 'BSD' in platform.system():
            man_window_name = 'less'

        for i in range(10):
            self.session.server._update_windows()
            if w.get('window_name') != man_window_name:
                break
            time.sleep(.2)

        self.assertNotEqual(w.get('window_name'), man_window_name)

        pane_base_index = w.show_window_option('pane-base-index', g=True)
        w.select_pane(pane_base_index)

        for i in range(10):
            self.session.server._update_windows()
            if w.get('window_name') == man_window_name:
                break
            time.sleep(.2)

        self.assertEqual(w.get('window_name'), text_type(man_window_name))

        w.select_pane('-D')
        for i in range(10):
            self.session.server._update_windows()
            if w['window_name'] != man_window_name:
                break
            time.sleep(.2)

        self.assertNotEqual(w.get('window_name'), text_type(man_window_name))


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
      window_index: 1
      start_directory: /usr/bin
      layout: main-horizontal
      options:
          main-pane-height: 50
      panes:
      - shell_command:
        - echo "hey"
      - shell_command:
        - echo "moo"
    - window_name: support to be /dev
      window_index: 2
      start_directory: /dev
      layout: main-horizontal
      panes:
      - shell_command:
        - pwd
      - shell_command:
        - echo "hey"
      - shell_command:
        - echo "moo"
    - window_name: cwd containing a space
      window_index: 3
      start_directory: {TEST_DIR}
      layout: main-horizontal
      panes:
      - shell_command:
        - pwd
      - shell_command:
        - echo "hey"
      - shell_command:
        - echo "moo"
    - window_name: testsa3
      window_index: 4
      layout: main-horizontal
      panes:
      - shell_command:
        - pwd
      - shell_command:
        - echo "hey"
      - shell_command:
        - echo "moo3"
    - window_name: cwd relative to start_directory since no rel dir entered
      window_index: 5
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

        self.tempdir = tempfile.gettempdir()
        self.test_dir = os.path.join(self.tempdir, 'foo bar')

        if not os.path.exists(self.test_dir):
            os.mkdir(self.test_dir)
            self._temp_dir_created = True
        else:
            self._temp_dir_created = False

    def tearDown(self):
        super(StartDirectoryTest, self).tearDown()
        if self._temp_dir_created:
            os.rmdir(self.test_dir)

    def test_start_directory(self):

        test_config = self.yaml_config.format(
            TMP_DIR=self.tempdir,
            TEST_DIR=self.test_dir
        )

        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(test_config).get()
        sconfig = config.expand(sconfig)
        sconfig = config.trickle(sconfig)

        builder = WorkspaceBuilder(sconf=sconfig)
        builder.build(session=self.session)

        assert(self.session == builder.session)
        dirs = [
            '/usr/bin', '/dev', self.test_dir,
            '/usr',
            '/usr'
        ]

        for path, window in zip(dirs, self.session.windows):
            for p in window.panes:
                for i in range(60):
                    p.server._update_panes()
                    pane_path = p.get('pane_current_path')
                    if pane_path is None:
                        pass
                    elif (
                        path in pane_path or
                        pane_path == path
                    ):
                        result = (
                            path == pane_path or
                            path in pane_path
                        )
                        break
                    time.sleep(.2)

                # handle case with OS X adding /private/ to /tmp/ paths
                self.assertTrue(result)


class StartDirectoryRelativeTest(TmuxTestCase):
    """Same as above test, but with relative start directory, mimicing
    loading it from a location of project file. Like::

    $ tmuxp load ~/workspace/myproject/.tmuxp.yaml

    instead of::

    $ cd ~/workspace/myproject/.tmuxp.yaml
    $ tmuxp load .

    """

    yaml_config = """
    session_name: sampleconfig
    start_directory: ./
    windows:
    - window_name: supposed to be /usr/bin
      start_directory: '/usr/bin'
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
      start_directory: {TEST_DIR}
      layout: main-horizontal
      panes:
      - shell_command:
        - pwd
      - shell_command:
        - echo "hey"
      - shell_command:
        - echo "moo"
    - window_name: inherit start_directory which is rel to config file
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
        super(StartDirectoryRelativeTest, self).setUp()

        self.tempdir = tempfile.gettempdir()

        self.test_dir = os.path.join(self.tempdir, 'foo bar')
        self.config_dir = os.path.join(self.tempdir, 'testRelConfigDir')

        if (
            not os.path.exists(self.test_dir) or
            not os.path.exists(self.config_dir)
        ):
            os.mkdir(self.test_dir)
            os.mkdir(self.config_dir)
            self._temp_dir_created = True
        else:
            self._temp_dir_created = False

        assert(os.path.exists(self.config_dir))
        assert(os.path.exists(self.test_dir))

    def tearDown(self):
        super(StartDirectoryRelativeTest, self).tearDown()
        if self._temp_dir_created:
            os.rmdir(self.test_dir)
            os.rmdir(self.config_dir)

    def test_start_directory(self):

        test_config = self.yaml_config.format(
            TEST_DIR=self.test_dir,
        )

        start_directory = os.getcwd()

        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(test_config).get()
        # the second argument of os.getcwd() mimics the behavior
        # the CLI loader will do, but it passes in the config file's location.
        sconfig = config.expand(sconfig, self.config_dir)

        sconfig = config.trickle(sconfig)

        assert(os.path.exists(self.config_dir))
        assert(os.path.exists(self.test_dir))
        builder = WorkspaceBuilder(sconf=sconfig)
        builder.build(session=self.session)

        assert(self.session == builder.session)

        dirs = [
            '/usr/bin',
            '/dev',
            self.test_dir,
            self.config_dir,
            self.config_dir,
        ]

        for path, window in zip(dirs, self.session.windows):
            for p in window.panes:
                for i in range(60):
                    p.server._update_panes()
                    # Handle case where directories resolve to /private/ in OSX
                    pane_path = p.get('pane_current_path')
                    if pane_path is None:
                        pass
                    elif (
                        path in pane_path or
                        pane_path == path
                    ):
                        result = (
                            path == pane_path or
                            path in pane_path
                        )

                        break
                    time.sleep(.2)

                self.assertTrue(result)


class PaneOrderingTest(TmuxTestCase):

    """Pane ordering based on position in config and ``pane_index``.

    Regression test for https://github.com/tony/tmuxp/issues/15.

    """

    yaml_config = """
    session_name: sampleconfig
    start_directory: {HOME}
    windows:
    - options:
      - automatic_rename: on
      layout: tiled
      panes:
      - cd /usr/bin
      - cd /usr
      - cd /sbin
      - cd {HOME}
    """.format(
        HOME=os.path.realpath(os.path.expanduser('~'))
    )

    def test_pane_order(self):

        # test order of `panes` (and pane_index) above aganist pane_dirs
        pane_paths = [
            '/usr/bin',
            '/usr',
            '/sbin',
            os.path.realpath(os.path.expanduser('~'))
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
    before_script: {script_not_exists}
    windows:
    - panes:
      - pane
    """

    config_script_fails = """
    session_name: sampleconfig
    before_script: {script_failed}
    windows:
    - panes:
      - pane
    """

    config_script_completes = """
    session_name: sampleconfig
    before_script: {script_complete}
    windows:
    - panes:
      - pane
    """

    def test_throw_error_if_retcode_error(self):

        sconfig = kaptan.Kaptan(handler='yaml')
        yaml = self.config_script_fails.format(
            fixtures_dir=fixtures_dir,
            script_failed=os.path.join(fixtures_dir, 'script_failed.sh')
        )

        sconfig = sconfig.import_config(yaml).get()
        sconfig = config.expand(sconfig)
        sconfig = config.trickle(sconfig)

        builder = WorkspaceBuilder(sconf=sconfig)

        with self.temp_session() as sess:
            session_name = sess.get('session_name')

            with self.assertRaises(exc.BeforeLoadScriptError):
                builder.build(session=sess)

            result = self.server.has_session(session_name)
            self.assertFalse(
                result,
                msg="Kills session if before_script exits with errcode"
            )

    def test_throw_error_if_file_not_exists(self):

        sconfig = kaptan.Kaptan(handler='yaml')
        yaml = self.config_script_not_exists.format(
            fixtures_dir=fixtures_dir,
            script_not_exists=os.path.join(fixtures_dir, 'script_not_exists.sh')
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
                (exc.BeforeLoadScriptNotExists, OSError),
                'No such file or directory'
            ):
                builder.build(session=sess)
            result = self.server.has_session(session_name)
            self.assertFalse(
                result,
                msg="Kills session if before_script doesn't exist"
            )

    def test_true_if_test_passes(self):
        assert(os.path.exists(os.path.join(fixtures_dir, 'script_complete.sh')))
        sconfig = kaptan.Kaptan(handler='yaml')
        yaml = self.config_script_completes.format(
            fixtures_dir=fixtures_dir,
            script_complete=os.path.join(fixtures_dir, 'script_complete.sh')
        )

        sconfig = sconfig.import_config(yaml).get()
        sconfig = config.expand(sconfig)
        sconfig = config.trickle(sconfig)

        builder = WorkspaceBuilder(sconf=sconfig)

        with self.temp_session() as session:
            builder.build(session=self.session)

    def test_true_if_test_passes_with_args(self):
        assert(os.path.exists(os.path.join(fixtures_dir, 'script_complete.sh')))
        sconfig = kaptan.Kaptan(handler='yaml')
        yaml = self.config_script_completes.format(
            fixtures_dir=fixtures_dir,
            script_complete=os.path.join(fixtures_dir, 'script_complete.sh') + ' -v'
        )

        sconfig = sconfig.import_config(yaml).get()
        sconfig = config.expand(sconfig)
        sconfig = config.trickle(sconfig)

        builder = WorkspaceBuilder(sconf=sconfig)

        with self.temp_session() as session:
            builder.build(session=self.session)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BeforeLoadScript))
    suite.addTest(unittest.makeSuite(BlankPaneTest))
    suite.addTest(unittest.makeSuite(FocusAndPaneIndexTest))
    suite.addTest(unittest.makeSuite(PaneOrderingTest))
    suite.addTest(unittest.makeSuite(StartDirectoryTest))
    suite.addTest(unittest.makeSuite(StartDirectoryRelativeTest))
    suite.addTest(unittest.makeSuite(ThreePaneTest))
    suite.addTest(unittest.makeSuite(TwoPaneTest))
    suite.addTest(unittest.makeSuite(WindowAutomaticRename))
    suite.addTest(unittest.makeSuite(WindowIndexTest))
    suite.addTest(unittest.makeSuite(WindowOptions))
    return suite
