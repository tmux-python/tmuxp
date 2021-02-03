# -*- coding: utf-8 -*-
"""Test for tmuxp workspacebuilder."""

from __future__ import absolute_import, unicode_literals

import os

import pytest

import kaptan

from libtmux import Window
from libtmux.common import has_gte_version
from libtmux.test import retry, temp_session
from tmuxp import config, exc
from tmuxp._compat import text_type
from tmuxp.cli import load_plugins
from tmuxp.workspacebuilder import WorkspaceBuilder

from . import example_dir, fixtures_dir
from .fixtures._util import loadfixture


def test_split_windows(session):
    yaml_config = loadfixture("workspacebuilder/two_pane.yaml")
    s = session
    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(yaml_config).get()

    builder = WorkspaceBuilder(sconf=sconfig)

    window_count = len(session._windows)  # current window count
    assert len(s._windows) == window_count
    for w, wconf in builder.iter_create_windows(s):
        for p in builder.iter_create_panes(w, wconf):
            w.select_layout('tiled')  # fix glitch with pane size
            p = p
            assert len(s._windows) == window_count
        assert isinstance(w, Window)

        assert len(s._windows) == window_count
        window_count += 1


def test_split_windows_three_pane(session):
    yaml_config = loadfixture("workspacebuilder/three_pane.yaml")

    s = session
    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(yaml_config).get()

    builder = WorkspaceBuilder(sconf=sconfig)

    window_count = len(s._windows)  # current window count
    assert len(s._windows) == window_count
    for w, wconf in builder.iter_create_windows(s):
        for p in builder.iter_create_panes(w, wconf):
            w.select_layout('tiled')  # fix glitch with pane size
            p = p
            assert len(s._windows) == window_count
        assert isinstance(w, Window)

        assert len(s._windows) == window_count
        window_count += 1
        w.set_window_option('main-pane-height', 50)
        w.select_layout(wconf['layout'])


def test_focus_pane_index(session):
    yaml_config = loadfixture('workspacebuilder/focus_and_pane.yaml')

    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(yaml_config).get()
    sconfig = config.expand(sconfig)
    sconfig = config.trickle(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig)

    builder.build(session=session)

    assert session.attached_window.name == 'focused window'

    pane_base_index = int(
        session.attached_window.show_window_option('pane-base-index', g=True)
    )

    if not pane_base_index:
        pane_base_index = 0
    else:
        pane_base_index = int(pane_base_index)

    # get the pane index for each pane
    pane_base_indexes = []
    for pane in session.attached_window.panes:
        pane_base_indexes.append(int(pane.index))

    pane_indexes_should_be = [pane_base_index + x for x in range(0, 3)]
    assert pane_indexes_should_be == pane_base_indexes

    w = session.attached_window

    assert w.name != 'man'

    pane_path = '/usr'

    while retry():
        p = w.attached_pane
        p.server._update_panes()
        if p.current_path == pane_path:
            break

    assert p.current_path == pane_path

    proc = session.cmd('show-option', '-gv', 'base-index')
    base_index = int(proc.stdout[0])
    session.server._update_windows()

    window3 = session.find_where({'window_index': str(base_index + 2)})
    assert isinstance(window3, Window)

    p = None
    pane_path = '/'

    while retry():
        p = window3.attached_pane
        p.server._update_panes()
        if p.current_path == pane_path:
            break

    assert p.current_path == pane_path


@pytest.mark.skip(
    reason='''
Test needs to be rewritten, assertion not reliable across platforms
and CI. See https://github.com/tmux-python/tmuxp/issues/310.
    '''.strip()
)
def test_suppress_history(session):
    yaml_config = loadfixture("workspacebuilder/suppress_history.yaml")
    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(yaml_config).get()
    sconfig = config.expand(sconfig)
    sconfig = config.trickle(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig)
    builder.build(session=session)

    inHistoryWindow = session.find_where({'window_name': 'inHistory'})
    isMissingWindow = session.find_where({'window_name': 'isMissing'})

    def assertHistory(cmd, hist):
        return 'inHistory' in cmd and cmd.endswith(hist)

    def assertIsMissing(cmd, hist):
        return 'isMissing' in cmd and not cmd.endswith(hist)

    for w, window_name, assertCase in [
        (inHistoryWindow, 'inHistory', assertHistory),
        (isMissingWindow, 'isMissing', assertIsMissing),
    ]:
        assert w.name == window_name
        correct = False
        w.select_window()
        p = w.attached_pane
        p.select_pane()

        # Print the last-in-history command in the pane
        p.cmd('send-keys', ' fc -ln -1')
        p.cmd('send-keys', 'Enter')

        buffer_name = 'test'
        while retry():
            # from v0.7.4 libtmux session.cmd adds target -t self.id by default
            # show-buffer doesn't accept -t, use global cmd.

            # Get the contents of the pane
            p.cmd('capture-pane', '-b', buffer_name)

            captured_pane = session.server.cmd('show-buffer', '-b', buffer_name)
            session.server.cmd('delete-buffer', '-b', buffer_name)

            # Parse the sent and last-in-history commands
            sent_cmd = captured_pane.stdout[0].strip()
            history_cmd = captured_pane.stdout[-2].strip()

            if assertCase(sent_cmd, history_cmd):
                correct = True
                break
        assert correct, "Unknown sent command: [%s] in %s" % (sent_cmd, assertCase)


def test_session_options(session):
    yaml_config = loadfixture("workspacebuilder/session_options.yaml")
    s = session
    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(yaml_config).get()
    sconfig = config.expand(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig)
    builder.build(session=session)

    assert "/bin/sh" in s.show_option('default-shell')
    assert "/bin/sh" in s.show_option('default-command')


def test_global_options(session):
    yaml_config = loadfixture("workspacebuilder/global_options.yaml")
    s = session
    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(yaml_config).get()
    sconfig = config.expand(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig)
    builder.build(session=session)

    assert "top" in s.show_option('status-position', _global=True)
    assert 493 == s.show_option('repeat-time', _global=True)


def test_global_session_env_options(session, monkeypatch):
    visual_silence = 'on'
    monkeypatch.setenv(str('VISUAL_SILENCE'), str(visual_silence))
    repeat_time = 738
    monkeypatch.setenv(str('REPEAT_TIME'), str(repeat_time))
    main_pane_height = 8
    monkeypatch.setenv(str('MAIN_PANE_HEIGHT'), str(main_pane_height))

    yaml_config = loadfixture("workspacebuilder/env_var_options.yaml")
    s = session
    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(yaml_config).get()
    sconfig = config.expand(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig)
    builder.build(session=session)

    assert visual_silence in s.show_option('visual-silence', _global=True)
    assert repeat_time == s.show_option('repeat-time')
    assert main_pane_height == s.attached_window.show_window_option('main-pane-height')


def test_window_options(session):
    yaml_config = loadfixture("workspacebuilder/window_options.yaml")
    s = session
    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(yaml_config).get()
    sconfig = config.expand(sconfig)

    if has_gte_version('2.3'):
        sconfig['windows'][0]['options']['pane-border-format'] = ' #P '

    builder = WorkspaceBuilder(sconf=sconfig)

    window_count = len(session._windows)  # current window count
    assert len(s._windows) == window_count
    for w, wconf in builder.iter_create_windows(s):
        for p in builder.iter_create_panes(w, wconf):
            w.select_layout('tiled')  # fix glitch with pane size
            p = p
            assert len(s._windows) == window_count
        assert isinstance(w, Window)
        assert w.show_window_option('main-pane-height') == 5
        if has_gte_version('2.3'):
            assert w.show_window_option('pane-border-format') == ' #P '

        assert len(s._windows) == window_count
        window_count += 1
        w.select_layout(wconf['layout'])


@pytest.mark.flaky(reruns=5)
def test_window_options_after(session):
    yaml_config = loadfixture("workspacebuilder/window_options_after.yaml")
    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(yaml_config).get()
    sconfig = config.expand(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig)
    builder.build(session=session)

    def assert_last_line(p, s):
        correct = False

        while retry():
            pane_out = p.cmd('capture-pane', '-p', '-J').stdout
            while not pane_out[-1].strip():  # delete trailing lines tmux 1.8
                pane_out.pop()
            if len(pane_out) > 1 and pane_out[-2].strip() == s:
                correct = True
                break

        # Print output for easier debugging if assertion fails
        if not correct:
            print('\n'.join(pane_out))

        return correct

    for i, pane in enumerate(session.attached_window.panes):
        assert assert_last_line(
            pane, str(i)
        ), "Initial command did not execute properly/" + str(i)
        pane.cmd('send-keys', 'Up')  # Will repeat echo
        pane.enter()  # in each iteration
        assert assert_last_line(
            pane, str(i)
        ), "Repeated command did not execute properly/" + str(i)

    session.cmd('send-keys', ' echo moo')
    session.cmd('send-keys', 'Enter')

    for pane in session.attached_window.panes:
        assert assert_last_line(
            pane, 'moo'
        ), "Synchronized command did not execute properly"


def test_window_shell(session):
    yaml_config = loadfixture("workspacebuilder/window_shell.yaml")
    s = session
    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(yaml_config).get()
    sconfig = config.expand(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig)

    for w, wconf in builder.iter_create_windows(s):
        if 'window_shell' in wconf:
            assert wconf['window_shell'] == text_type('top')

        while retry():
            session.server._update_windows()
            if w['window_name'] != 'top':
                break

        assert w.name != text_type('top')


def test_environment_variables(session):
    yaml_config = loadfixture("workspacebuilder/environment_vars.yaml")
    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(yaml_config).get()
    sconfig = config.expand(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig)
    builder.build(session)

    assert session.show_environment('FOO') == 'BAR'
    assert session.show_environment('PATH') == '/tmp'


def test_automatic_rename_option(session):
    """With option automatic-rename: on."""
    yaml_config = loadfixture("workspacebuilder/window_automatic_rename.yaml")
    s = session
    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(yaml_config).get()

    builder = WorkspaceBuilder(sconf=sconfig)

    window_count = len(session._windows)  # current window count
    assert len(s._windows) == window_count
    for w, wconf in builder.iter_create_windows(s):

        for p in builder.iter_create_panes(w, wconf):
            w.select_layout('tiled')  # fix glitch with pane size
            p = p
            assert len(s._windows), window_count
        assert isinstance(w, Window)
        assert w.show_window_option('automatic-rename') == 'on'

        assert len(s._windows) == window_count

        window_count += 1
        w.select_layout(wconf['layout'])

    assert s.name != 'tmuxp'
    w = s.windows[0]

    while retry():
        session.server._update_windows()
        if w.name != 'sh':
            break

    assert w.name != 'sh'

    pane_base_index = w.show_window_option('pane-base-index', g=True)
    w.select_pane(pane_base_index)

    while retry():
        session.server._update_windows()
        if w.name == 'sh':
            break

    assert w.name == text_type('sh')

    w.select_pane('-D')

    while retry():
        session.server._update_windows()
        if w['window_name'] != 'sh':
            break

    assert w.name != text_type('sh')


def test_blank_pane_count(session):
    """:todo: Verify blank panes of various types build into workspaces."""
    yaml_config_file = os.path.join(example_dir, 'blank-panes.yaml')
    test_config = kaptan.Kaptan().import_config(yaml_config_file).get()
    test_config = config.expand(test_config)
    builder = WorkspaceBuilder(sconf=test_config)
    builder.build(session=session)

    assert session == builder.session

    window1 = session.find_where({'window_name': 'Blank pane test'})
    assert len(window1._panes) == 3

    window2 = session.find_where({'window_name': 'More blank panes'})
    assert len(window2._panes) == 3

    window3 = session.find_where({'window_name': 'Empty string (return)'})
    assert len(window3._panes) == 3

    window4 = session.find_where({'window_name': 'Blank with options'})
    assert len(window4._panes) == 2


def test_start_directory(session, tmpdir):
    yaml_config = loadfixture("workspacebuilder/start_directory.yaml")
    test_dir = str(tmpdir.mkdir('foo bar'))
    test_config = yaml_config.format(TMP_DIR=str(tmpdir), TEST_DIR=test_dir)

    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(test_config).get()
    sconfig = config.expand(sconfig)
    sconfig = config.trickle(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig)
    builder.build(session=session)

    assert session == builder.session
    dirs = ['/usr/bin', '/dev', test_dir, '/usr', '/usr']

    for path, window in zip(dirs, session.windows):
        for p in window.panes:
            while retry():
                p.server._update_panes()
                pane_path = p.current_path
                if pane_path is None:
                    pass
                elif path in pane_path or pane_path == path:
                    result = path == pane_path or path in pane_path
                    break

            # handle case with OS X adding /private/ to /tmp/ paths
            assert result


def test_start_directory_relative(session, tmpdir):
    """Same as above test, but with relative start directory, mimicking
    loading it from a location of project file. Like::

    $ tmuxp load ~/workspace/myproject/.tmuxp.yaml

    instead of::

    $ cd ~/workspace/myproject/.tmuxp.yaml
    $ tmuxp load .

    """
    yaml_config = loadfixture("workspacebuilder/start_directory_relative.yaml")

    test_dir = str(tmpdir.mkdir('foo bar'))
    config_dir = str(tmpdir.mkdir('testRelConfigDir'))
    test_config = yaml_config.format(TEST_DIR=test_dir)

    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(test_config).get()
    # the second argument of os.getcwd() mimics the behavior
    # the CLI loader will do, but it passes in the config file's location.
    sconfig = config.expand(sconfig, config_dir)

    sconfig = config.trickle(sconfig)

    assert os.path.exists(config_dir)
    assert os.path.exists(test_dir)
    builder = WorkspaceBuilder(sconf=sconfig)
    builder.build(session=session)

    assert session == builder.session

    dirs = ['/usr/bin', '/dev', test_dir, config_dir, config_dir]

    for path, window in zip(dirs, session.windows):
        for p in window.panes:
            while retry():
                p.server._update_panes()
                # Handle case where directories resolve to /private/ in OSX
                pane_path = p.current_path
                if pane_path is None:
                    pass
                elif path in pane_path or pane_path == path:
                    result = path == pane_path or path in pane_path
                    break

            assert result


def test_pane_order(session):
    """Pane ordering based on position in config and ``pane_index``.

    Regression test for https://github.com/tmux-python/tmuxp/issues/15.

    """

    yaml_config = loadfixture("workspacebuilder/pane_ordering.yaml").format(
        HOME=os.path.realpath(os.path.expanduser('~'))
    )

    # test order of `panes` (and pane_index) above aganist pane_dirs
    pane_paths = [
        '/usr/bin',
        '/usr',
        '/usr/sbin',
        os.path.realpath(os.path.expanduser('~')),
    ]

    s = session
    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(yaml_config).get()
    sconfig = config.expand(sconfig)
    sconfig = config.trickle(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig)

    window_count = len(session._windows)  # current window count
    assert len(s._windows) == window_count
    for w, wconf in builder.iter_create_windows(s):
        for p in builder.iter_create_panes(w, wconf):
            w.select_layout('tiled')  # fix glitch with pane size
            p = p
            assert len(s._windows) == window_count

        assert isinstance(w, Window)

        assert len(s._windows) == window_count
        window_count += 1

    for w in session.windows:
        pane_base_index = w.show_window_option('pane-base-index', g=True)
        for p_index, p in enumerate(w.list_panes(), start=pane_base_index):
            assert int(p_index) == int(p.index)

            # pane-base-index start at base-index, pane_paths always start
            # at 0 since python list.
            pane_path = pane_paths[p_index - pane_base_index]

            while retry():
                p.server._update_panes()
                if p.current_path == pane_path:
                    break

            assert p.current_path, pane_path


def test_window_index(session):
    yaml_config = loadfixture("workspacebuilder/window_index.yaml")
    proc = session.cmd('show-option', '-gv', 'base-index')
    base_index = int(proc.stdout[0])
    name_index_map = {'zero': 0 + base_index, 'one': 1 + base_index, 'five': 5}

    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(yaml_config).get()
    sconfig = config.expand(sconfig)
    sconfig = config.trickle(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig)

    for window, _ in builder.iter_create_windows(session):
        expected_index = name_index_map[window['window_name']]
        assert int(window['window_index']) == expected_index


def test_before_load_throw_error_if_retcode_error(server):
    config_script_fails = loadfixture("workspacebuilder/config_script_fails.yaml")
    sconfig = kaptan.Kaptan(handler='yaml')
    yaml = config_script_fails.format(
        fixtures_dir=fixtures_dir,
        script_failed=os.path.join(fixtures_dir, 'script_failed.sh'),
    )

    sconfig = sconfig.import_config(yaml).get()
    sconfig = config.expand(sconfig)
    sconfig = config.trickle(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig)

    with temp_session(server) as sess:
        session_name = sess.name

        with pytest.raises(exc.BeforeLoadScriptError):
            builder.build(session=sess)

        result = server.has_session(session_name)
        assert not result, "Kills session if before_script exits with errcode"


def test_before_load_throw_error_if_file_not_exists(server):
    config_script_not_exists = loadfixture(
        "workspacebuilder/config_script_not_exists.yaml"
    )
    sconfig = kaptan.Kaptan(handler='yaml')
    yaml = config_script_not_exists.format(
        fixtures_dir=fixtures_dir,
        script_not_exists=os.path.join(fixtures_dir, 'script_not_exists.sh'),
    )
    sconfig = sconfig.import_config(yaml).get()
    sconfig = config.expand(sconfig)
    sconfig = config.trickle(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig)

    with temp_session(server) as sess:
        session_name = sess.name
        temp_session_exists = server.has_session(sess.name)
        assert temp_session_exists
        with pytest.raises((exc.BeforeLoadScriptNotExists, OSError)) as excinfo:
            builder.build(session=sess)
            excinfo.match(r'No such file or directory')
        result = server.has_session(session_name)
        assert not result, "Kills session if before_script doesn't exist"


def test_before_load_true_if_test_passes(server):
    config_script_completes = loadfixture(
        "workspacebuilder/config_script_completes.yaml"
    )
    assert os.path.exists(os.path.join(fixtures_dir, 'script_complete.sh'))
    sconfig = kaptan.Kaptan(handler='yaml')
    yaml = config_script_completes.format(
        fixtures_dir=fixtures_dir,
        script_complete=os.path.join(fixtures_dir, 'script_complete.sh'),
    )

    sconfig = sconfig.import_config(yaml).get()
    sconfig = config.expand(sconfig)
    sconfig = config.trickle(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig)

    with temp_session(server) as session:
        builder.build(session=session)


def test_before_load_true_if_test_passes_with_args(server):
    config_script_completes = loadfixture(
        "workspacebuilder/config_script_completes.yaml"
    )

    assert os.path.exists(os.path.join(fixtures_dir, 'script_complete.sh'))
    sconfig = kaptan.Kaptan(handler='yaml')
    yaml = config_script_completes.format(
        fixtures_dir=fixtures_dir,
        script_complete=os.path.join(fixtures_dir, 'script_complete.sh') + ' -v',
    )

    sconfig = sconfig.import_config(yaml).get()
    sconfig = config.expand(sconfig)
    sconfig = config.trickle(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig)

    with temp_session(server) as session:
        builder.build(session=session)


def test_plugin_system_before_workspace_builder(
    monkeypatch_plugin_test_packages, session
):
    config_plugins = loadfixture("workspacebuilder/plugin_bwb.yaml")

    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(config_plugins).get()
    sconfig = config.expand(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig, plugins=load_plugins(sconfig))
    assert len(builder.plugins) > 0

    builder.build(session=session)

    proc = session.cmd('display-message', '-p', "'#S'")
    assert proc.stdout[0] == "'plugin_test_bwb'"


def test_plugin_system_on_window_create(monkeypatch_plugin_test_packages, session):
    config_plugins = loadfixture("workspacebuilder/plugin_owc.yaml")

    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(config_plugins).get()
    sconfig = config.expand(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig, plugins=load_plugins(sconfig))
    assert len(builder.plugins) > 0

    builder.build(session=session)

    proc = session.cmd('display-message', '-p', "'#W'")
    assert proc.stdout[0] == "'plugin_test_owc'"


def test_plugin_system_after_window_finished(monkeypatch_plugin_test_packages, session):
    config_plugins = loadfixture("workspacebuilder/plugin_awf.yaml")

    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(config_plugins).get()
    sconfig = config.expand(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig, plugins=load_plugins(sconfig))
    assert len(builder.plugins) > 0

    builder.build(session=session)

    proc = session.cmd('display-message', '-p', "'#W'")
    assert proc.stdout[0] == "'plugin_test_awf'"


def test_plugin_system_on_window_create_multiple_windows(session):
    config_plugins = loadfixture("workspacebuilder/plugin_owc_multiple_windows.yaml")

    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(config_plugins).get()
    sconfig = config.expand(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig, plugins=load_plugins(sconfig))
    assert len(builder.plugins) > 0

    builder.build(session=session)

    proc = session.cmd('list-windows', '-F', "'#W'")
    assert "'plugin_test_owc_mw'" in proc.stdout
    assert "'plugin_test_owc_mw_2'" in proc.stdout


def test_plugin_system_after_window_finished_multiple_windows(
    monkeypatch_plugin_test_packages, session
):
    config_plugins = loadfixture("workspacebuilder/plugin_awf_multiple_windows.yaml")

    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(config_plugins).get()
    sconfig = config.expand(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig, plugins=load_plugins(sconfig))
    assert len(builder.plugins) > 0

    builder.build(session=session)

    proc = session.cmd('list-windows', '-F', "'#W'")
    assert "'plugin_test_awf_mw'" in proc.stdout
    assert "'plugin_test_awf_mw_2'" in proc.stdout


def test_plugin_system_multiple_plugins(monkeypatch_plugin_test_packages, session):
    config_plugins = loadfixture("workspacebuilder/plugin_multiple_plugins.yaml")

    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(config_plugins).get()
    sconfig = config.expand(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig, plugins=load_plugins(sconfig))
    assert len(builder.plugins) > 0

    builder.build(session=session)

    # Drop through to the before_script plugin hook
    proc = session.cmd('display-message', '-p', "'#S'")
    assert proc.stdout[0] == "'plugin_test_bwb'"

    # Drop through to the after_window_finished. This won't succeed
    # unless on_window_create succeeds because of how the test plugin
    # override methods are currently written
    proc = session.cmd('display-message', '-p', "'#W'")
    assert proc.stdout[0] == "'mp_test_awf'"


def test_load_configs_same_session(server):
    yaml_config = loadfixture("workspacebuilder/three_windows.yaml")
    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(yaml_config).get()

    builder = WorkspaceBuilder(sconf=sconfig, server=server)
    builder.build()

    assert len(server.sessions) == 1
    assert len(server.sessions[0]._windows) == 3

    yaml_config = loadfixture("workspacebuilder/two_windows.yaml")

    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(yaml_config).get()

    builder = WorkspaceBuilder(sconf=sconfig, server=server)
    builder.build()
    assert len(server.sessions) == 2
    assert len(server.sessions[1]._windows) == 2

    yaml_config = loadfixture("workspacebuilder/two_windows.yaml")

    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(yaml_config).get()

    builder = WorkspaceBuilder(sconf=sconfig, server=server)
    builder.build(server.sessions[1], True)

    assert len(server.sessions) == 2
    assert len(server.sessions[1]._windows) == 4


def test_load_configs_separate_sessions(server):
    yaml_config = loadfixture("workspacebuilder/three_windows.yaml")
    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(yaml_config).get()

    builder = WorkspaceBuilder(sconf=sconfig, server=server)
    builder.build()

    assert len(server.sessions) == 1
    assert len(server.sessions[0]._windows) == 3

    yaml_config = loadfixture("workspacebuilder/two_windows.yaml")

    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(yaml_config).get()

    builder = WorkspaceBuilder(sconf=sconfig, server=server)
    builder.build()

    assert len(server.sessions) == 2
    assert len(server.sessions[0]._windows) == 3
    assert len(server.sessions[1]._windows) == 2


def test_find_current_active_pane(server, monkeypatch):
    yaml_config = loadfixture("workspacebuilder/three_windows.yaml")
    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(yaml_config).get()

    builder = WorkspaceBuilder(sconf=sconfig, server=server)
    builder.build()

    yaml_config = loadfixture("workspacebuilder/two_windows.yaml")

    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(yaml_config).get()

    builder = WorkspaceBuilder(sconf=sconfig, server=server)
    builder.build()

    assert len(server.list_sessions()) == 2

    # Assign an active pane to the session
    second_session = server.list_sessions()[1]
    first_pane_on_second_session_id = second_session.list_windows()[0].list_panes()[0][
        "pane_id"
    ]
    monkeypatch.setenv("TMUX_PANE", first_pane_on_second_session_id)

    builder = WorkspaceBuilder(sconf=sconfig, server=server)

    assert builder.find_current_attached_session() == second_session
