# -*- coding: utf-8 -*-
"""Test for tmuxp workspacebuilder."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals, with_statement)

import logging
import os
import tempfile
import time

import kaptan
import pytest
from flaky import flaky

from tmuxp import Window, config, exc
from tmuxp._compat import text_type
from tmuxp.workspacebuilder import WorkspaceBuilder

from .fixtures._util import loadfixture
from .helpers import TmuxTestCase, example_dir, fixtures_dir, mute

logger = logging.getLogger(__name__)


class TwoPaneTest(TmuxTestCase):

    yaml_config = loadfixture("workspacebuilder/two_pane.yaml")

    def test_split_windows(self):
        s = self.session
        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(self.yaml_config).get()

        builder = WorkspaceBuilder(sconf=sconfig)

        window_count = len(self.session._windows)  # current window count
        assert len(s._windows) == window_count
        for w, wconf in builder.iter_create_windows(s):
            for p in builder.iter_create_panes(w, wconf):
                p = p
                assert len(s._windows) == window_count
            assert isinstance(w, Window)

            assert len(s._windows) == window_count
            window_count += 1


class ThreePaneTest(TmuxTestCase):

    yaml_config = loadfixture("workspacebuilder/three_pane.yaml")

    def test_split_windows(self):
        s = self.session
        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(self.yaml_config).get()

        builder = WorkspaceBuilder(sconf=sconfig)

        window_count = len(self.session._windows)  # current window count
        assert len(s._windows) == window_count
        for w, wconf in builder.iter_create_windows(s):
            for p in builder.iter_create_panes(w, wconf):
                p = p
                assert len(s._windows) == window_count
            assert isinstance(w, Window)

            assert len(s._windows) == window_count
            window_count += 1
            w.set_window_option('main-pane-height', 50)
            w.select_layout(wconf['layout'])


class FocusAndPaneIndexTest(TmuxTestCase):

    yaml_config = loadfixture('workspacebuilder/focus_and_pane.yaml')

    def test_focus_pane_index(self):
        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(self.yaml_config).get()
        sconfig = config.expand(sconfig)
        sconfig = config.trickle(sconfig)

        builder = WorkspaceBuilder(sconf=sconfig)

        builder.build(session=self.session)

        assert self.session.attached_window().get('window_name') == \
            'focused window'

        pane_base_index = int(
            self.session.attached_window().show_window_option(
                'pane-base-index', g=True
            )
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
        assert pane_indexes_should_be == pane_base_indexes

        w = self.session.attached_window()

        assert w.get('window_name') != 'man'

        pane_path = '/usr'
        for i in range(20):
            p = w.attached_pane()
            p.server._update_panes()
            if p.get('pane_current_path') == pane_path:
                break
            time.sleep(.4)

        assert p.get('pane_current_path') == pane_path

        proc = self.session.cmd('show-option', '-gv', 'base-index')
        base_index = int(proc.stdout[0])
        self.session.server._update_windows()

        window3 = self.session.findWhere({'window_index': str(base_index + 2)})
        assert isinstance(window3, Window)

        p = None
        pane_path = '/'
        for i in range(10):
            p = window3.attached_pane()
            p.server._update_panes()
            if p.get('pane_current_path') == pane_path:
                break
            time.sleep(.4)

        assert p.get('pane_current_path') == pane_path


class SuppressHistoryTest(TmuxTestCase):
    yaml_config = loadfixture("workspacebuilder/suppress_history.yaml")

    @flaky(max_runs=5, min_passes=1)
    def test_suppress_history(self):
        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(self.yaml_config).get()
        sconfig = config.expand(sconfig)
        sconfig = config.trickle(sconfig)

        builder = WorkspaceBuilder(sconf=sconfig)
        builder.build(session=self.session)

        inHistoryPane = self.session.findWhere(
            {'window_name': 'inHistory'}).attached_pane()
        isMissingPane = self.session.findWhere(
            {'window_name': 'isMissing'}).attached_pane()

        def assertHistory(cmd, hist):
            return 'inHistory' in cmd and cmd == hist

        def assertIsMissing(cmd, hist):
            return 'isMissing' in cmd and cmd != hist

        for p, assertCase in [
            (inHistoryPane, assertHistory,), (isMissingPane, assertIsMissing,)
        ]:
            correct = False
            p.window.select_window()
            p.select_pane()

            # Print the last-in-history command in the pane
            self.session.cmd('send-keys', ' fc -ln -1')
            self.session.cmd('send-keys', 'Enter')

            for i in range(10):
                time.sleep(0.1)

                # Get the contents of the pane
                self.session.cmd('capture-pane')
                captured_pane = self.session.cmd('show-buffer')
                self.session.cmd('delete-buffer')

                # Parse the sent and last-in-history commands
                sent_cmd = captured_pane.stdout[0].strip()
                history_cmd = captured_pane.stdout[-2].strip()

                if assertCase(sent_cmd, history_cmd):
                    correct = True
                    break
            assert correct, "Unknown sent command: [%s]" % sent_cmd


class WindowOptions(TmuxTestCase):

    yaml_config = loadfixture("workspacebuilder/window_options.yaml")

    def test_window_options(self):
        s = self.session
        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(self.yaml_config).get()
        sconfig = config.expand(sconfig)

        builder = WorkspaceBuilder(sconf=sconfig)

        window_count = len(self.session._windows)  # current window count
        assert len(s._windows) == window_count
        for w, wconf in builder.iter_create_windows(s):
            for p in builder.iter_create_panes(w, wconf):
                p = p
                assert len(s._windows) == window_count
            assert isinstance(w, Window)
            assert w.show_window_option('main-pane-height') == 5

            assert len(s._windows) == window_count
            window_count += 1
            w.select_layout(wconf['layout'])

    def test_window_shell(self):
        yaml_config = loadfixture("workspacebuilder/window_shell.yaml")
        s = self.session
        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(yaml_config).get()
        sconfig = config.expand(sconfig)

        builder = WorkspaceBuilder(sconf=sconfig)

        for w, wconf in builder.iter_create_windows(s):
            if 'window_shell' in wconf:
                assert wconf['window_shell'] == text_type('top')
            for i in range(10):
                self.session.server._update_windows()
                if w['window_name'] != 'top':
                    break
                time.sleep(.2)

            assert w.get('window_name') != text_type('top')


class EnvironmentVariables(TmuxTestCase):

    yaml_config = loadfixture("workspacebuilder/environment_vars.yaml")

    def test_environment_variables(self):
        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(self.yaml_config).get()
        sconfig = config.expand(sconfig)

        builder = WorkspaceBuilder(sconf=sconfig)
        builder.build(self.session)

        assert self.session.show_environment('FOO') == 'BAR'
        assert self.session.show_environment('PATH') == '/tmp'


class WindowAutomaticRename(TmuxTestCase):

    yaml_config = loadfixture("workspacebuilder/window_automatic_rename.yaml")

    def test_automatic_rename_option(self):
        """With option automatic-rename: on."""
        s = self.session
        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(self.yaml_config).get()

        builder = WorkspaceBuilder(sconf=sconfig)

        window_count = len(self.session._windows)  # current window count
        assert len(s._windows) == window_count
        for w, wconf in builder.iter_create_windows(s):
            for p in builder.iter_create_panes(w, wconf):
                p = p
                assert len(s._windows), window_count
            assert isinstance(w, Window)
            assert w.show_window_option('automatic-rename') == 'on'

            assert len(s._windows) == window_count

            window_count += 1
            w.select_layout(wconf['layout'])

        assert s.get('session_name') != 'tmuxp'
        w = s.windows[0]

        for i in range(10):
            self.session.server._update_windows()
            if w.get('window_name') != 'sh':
                break
            time.sleep(.2)

        assert w.get('window_name') != 'sh'

        pane_base_index = w.show_window_option('pane-base-index', g=True)
        w.select_pane(pane_base_index)

        for i in range(10):
            self.session.server._update_windows()
            if w.get('window_name') == 'sh':
                break
            time.sleep(.3)

        assert w.get('window_name') == text_type('sh')

        w.select_pane('-D')
        for i in range(10):
            self.session.server._update_windows()
            if w['window_name'] != 'sh':
                break
            time.sleep(.2)

        assert w.get('window_name') != text_type('sh')


class BlankPaneTest(TmuxTestCase):

    """:todo: Verify blank panes of various types build into workspaces."""

    yaml_config_file = os.path.join(example_dir, 'blank-panes.yaml')

    def test_blank_pane_count(self):

        test_config = kaptan.Kaptan().import_config(
            self.yaml_config_file).get()
        test_config = config.expand(test_config)
        builder = WorkspaceBuilder(sconf=test_config)
        builder.build(session=self.session)

        assert self.session == builder.session

        window1 = self.session.findWhere({'window_name': 'Blank pane test'})
        assert len(window1._panes) == 3

        window2 = self.session.findWhere({'window_name': 'More blank panes'})
        assert len(window2._panes) == 3

        window3 = self.session.findWhere(
            {'window_name': 'Empty string (return)'}
        )
        assert len(window3._panes) == 3

        window4 = self.session.findWhere({'window_name': 'Blank with options'})
        assert len(window4._panes) == 2


class StartDirectoryTest(TmuxTestCase):
    yaml_config = loadfixture("workspacebuilder/start_directory.yaml")

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

        assert self.session == builder.session
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
                assert result


class StartDirectoryRelativeTest(TmuxTestCase):
    """Same as above test, but with relative start directory, mimicing
    loading it from a location of project file. Like::

    $ tmuxp load ~/workspace/myproject/.tmuxp.yaml

    instead of::

    $ cd ~/workspace/myproject/.tmuxp.yaml
    $ tmuxp load .

    """

    yaml_config = \
        loadfixture("workspacebuilder/start_directory_relative.yaml")

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

        assert os.path.exists(self.config_dir)
        assert os.path.exists(self.test_dir)

    def tearDown(self):
        super(StartDirectoryRelativeTest, self).tearDown()
        if self._temp_dir_created:
            os.rmdir(self.test_dir)
            os.rmdir(self.config_dir)

    def test_start_directory(self):

        test_config = self.yaml_config.format(
            TEST_DIR=self.test_dir,
        )

        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(test_config).get()
        # the second argument of os.getcwd() mimics the behavior
        # the CLI loader will do, but it passes in the config file's location.
        sconfig = config.expand(sconfig, self.config_dir)

        sconfig = config.trickle(sconfig)

        assert os.path.exists(self.config_dir)
        assert os.path.exists(self.test_dir)
        builder = WorkspaceBuilder(sconf=sconfig)
        builder.build(session=self.session)

        assert self.session == builder.session

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

                assert result


class PaneOrderingTest(TmuxTestCase):

    """Pane ordering based on position in config and ``pane_index``.

    Regression test for https://github.com/tony/tmuxp/issues/15.

    """

    yaml_config = loadfixture("workspacebuilder/pane_ordering.yaml").format(
        HOME=os.path.realpath(os.path.expanduser('~'))
    )

    def test_pane_order(self):

        # test order of `panes` (and pane_index) above aganist pane_dirs
        pane_paths = [
            '/usr/bin',
            '/usr',
            '/usr/sbin',
            os.path.realpath(os.path.expanduser('~'))
        ]

        s = self.session
        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(self.yaml_config).get()
        sconfig = config.expand(sconfig)
        sconfig = config.trickle(sconfig)

        builder = WorkspaceBuilder(sconf=sconfig)

        window_count = len(self.session._windows)  # current window count
        assert len(s._windows) == window_count
        for w, wconf in builder.iter_create_windows(s):
            for p in builder.iter_create_panes(w, wconf):
                p = p
                assert len(s._windows) == window_count

            assert isinstance(w, Window)

            assert len(s._windows) == window_count
            window_count += 1

        for w in self.session.windows:
            pane_base_index = w.show_window_option('pane-base-index', g=True)
            for p_index, p in enumerate(w.list_panes(), start=pane_base_index):
                assert int(p_index) == int(p.get('pane_index'))

                # pane-base-index start at base-index, pane_paths always start
                # at 0 since python list.
                pane_path = pane_paths[p_index - pane_base_index]

                for i in range(60):
                    p.server._update_panes()
                    if p.get('pane_current_path') == pane_path:
                        break
                    time.sleep(.2)

                assert p.get('pane_current_path'), pane_path


class WindowIndexTest(TmuxTestCase):
    yaml_config = loadfixture("workspacebuilder/window_index.yaml")

    def test_window_index(self):
        proc = self.session.cmd('show-option', '-gv', 'base-index')
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
            assert int(window['window_index']) == expected_index


class BeforeLoadScript(TmuxTestCase):
    config = 'HI'
    config_script_not_exists = loadfixture(
        "workspacebuilder/config_script_not_exists.yaml"
    )
    config_script_fails = loadfixture(
        "workspacebuilder/config_script_fails.yaml"
    )
    config_script_completes = loadfixture(
        "workspacebuilder/config_script_completes.yaml"
    )

    @mute()
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

            with pytest.raises(exc.BeforeLoadScriptError):
                builder.build(session=sess)

            result = self.server.has_session(session_name)
            assert not result, \
                "Kills session if before_script exits with errcode"

    @mute()
    def test_throw_error_if_file_not_exists(self):
        sconfig = kaptan.Kaptan(handler='yaml')
        yaml = self.config_script_not_exists.format(
            fixtures_dir=fixtures_dir,
            script_not_exists=os.path.join(
                fixtures_dir, 'script_not_exists.sh'
            )
        )
        sconfig = sconfig.import_config(yaml).get()
        sconfig = config.expand(sconfig)
        sconfig = config.trickle(sconfig)

        builder = WorkspaceBuilder(sconf=sconfig)

        with self.temp_session() as sess:
            session_name = sess.get('session_name')
            temp_session_exists = self.server.has_session(
                sess.get('session_name')
            )
            assert temp_session_exists
            with pytest.raises(
                (exc.BeforeLoadScriptNotExists, OSError),
            ) as excinfo:
                builder.build(session=sess)
                excinfo.match(r'No such file or directory')
            result = self.server.has_session(session_name)
            assert not result, "Kills session if before_script doesn't exist"

    @mute()
    def test_true_if_test_passes(self):
        assert os.path.exists(
            os.path.join(fixtures_dir, 'script_complete.sh'))
        sconfig = kaptan.Kaptan(handler='yaml')
        yaml = self.config_script_completes.format(
            fixtures_dir=fixtures_dir,
            script_complete=os.path.join(fixtures_dir, 'script_complete.sh')
        )

        sconfig = sconfig.import_config(yaml).get()
        sconfig = config.expand(sconfig)
        sconfig = config.trickle(sconfig)

        builder = WorkspaceBuilder(sconf=sconfig)

        with self.temp_session():
            builder.build(session=self.session)

    @mute()
    def test_true_if_test_passes_with_args(self):
        assert(
            os.path.exists(os.path.join(fixtures_dir, 'script_complete.sh'))
        )
        sconfig = kaptan.Kaptan(handler='yaml')
        yaml = self.config_script_completes.format(
            fixtures_dir=fixtures_dir,
            script_complete=os.path.join(
                fixtures_dir, 'script_complete.sh'
            ) + ' -v'
        )

        sconfig = sconfig.import_config(yaml).get()
        sconfig = config.expand(sconfig)
        sconfig = config.trickle(sconfig)

        builder = WorkspaceBuilder(sconf=sconfig)

        with self.temp_session():
            builder.build(session=self.session)
