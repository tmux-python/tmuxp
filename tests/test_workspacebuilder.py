"""Test for tmuxp workspacebuilder."""
import os
import pathlib
import textwrap
import time
import typing as t

import pytest

import libtmux
from libtmux.common import has_gte_version, has_lt_version
from libtmux.test import retry_until, temp_session
from libtmux.window import Window
from tmuxp import config, exc
from tmuxp.cli.load import load_plugins
from tmuxp.config_reader import ConfigReader
from tmuxp.workspacebuilder import WorkspaceBuilder

from .constants import EXAMPLE_PATH, FIXTURE_PATH
from .fixtures import utils as test_utils

if t.TYPE_CHECKING:
    from libtmux.server import Server


def test_split_windows(session):
    sconfig = ConfigReader._from_file(
        test_utils.get_config_file("workspacebuilder/two_pane.yaml")
    )

    builder = WorkspaceBuilder(sconf=sconfig)

    window_count = len(session._windows)  # current window count
    assert len(session._windows) == window_count
    for w, wconf in builder.iter_create_windows(session):
        for p in builder.iter_create_panes(w, wconf):
            w.select_layout("tiled")  # fix glitch with pane size
            p = p
            assert len(session._windows) == window_count
        assert isinstance(w, Window)

        assert len(session._windows) == window_count
        window_count += 1


def test_split_windows_three_pane(session):
    sconfig = ConfigReader._from_file(
        test_utils.get_config_file("workspacebuilder/three_pane.yaml")
    )

    builder = WorkspaceBuilder(sconf=sconfig)

    window_count = len(session._windows)  # current window count
    assert len(session._windows) == window_count
    for w, wconf in builder.iter_create_windows(session):
        for p in builder.iter_create_panes(w, wconf):
            w.select_layout("tiled")  # fix glitch with pane size
            p = p
            assert len(session._windows) == window_count
        assert isinstance(w, Window)

        assert len(session._windows) == window_count
        window_count += 1
        w.set_window_option("main-pane-height", 50)
        w.select_layout(wconf["layout"])


def test_focus_pane_index(session):
    sconfig = ConfigReader._from_file(
        test_utils.get_config_file("workspacebuilder/focus_and_pane.yaml")
    )
    sconfig = config.expand(sconfig)
    sconfig = config.trickle(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig)

    builder.build(session=session)

    assert session.attached_window.name == "focused window"

    pane_base_index = int(
        session.attached_window.show_window_option("pane-base-index", g=True)
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

    assert w.name != "man"

    pane_path = "/usr"
    p = None

    def f():
        nonlocal p
        p = w.attached_pane
        p.server._update_panes()
        return p.current_path == pane_path

    assert retry_until(f)

    assert p.current_path == pane_path

    proc = session.cmd("show-option", "-gv", "base-index")
    base_index = int(proc.stdout[0])
    session.server._update_windows()

    window3 = session.find_where({"window_index": str(base_index + 2)})
    assert isinstance(window3, Window)

    p = None
    pane_path = "/"

    def f():
        nonlocal p
        p = window3.attached_pane
        p.server._update_panes()
        return p.current_path == pane_path

    assert retry_until(f)

    assert p.current_path == pane_path


@pytest.mark.skip(
    reason="""
Test needs to be rewritten, assertion not reliable across platforms
and CI. See https://github.com/tmux-python/tmuxp/issues/310.
    """.strip()
)
def test_suppress_history(session):
    sconfig = ConfigReader._from_file(
        test_utils.get_config_file("workspacebuilder/suppress_history.yaml")
    )
    sconfig = config.expand(sconfig)
    sconfig = config.trickle(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig)
    builder.build(session=session)

    inHistoryWindow = session.find_where({"window_name": "inHistory"})
    isMissingWindow = session.find_where({"window_name": "isMissing"})

    def assertHistory(cmd, hist):
        return "inHistory" in cmd and cmd.endswith(hist)

    def assertIsMissing(cmd, hist):
        return "isMissing" in cmd and not cmd.endswith(hist)

    for w, window_name, assertCase in [
        (inHistoryWindow, "inHistory", assertHistory),
        (isMissingWindow, "isMissing", assertIsMissing),
    ]:
        assert w.name == window_name
        w.select_window()
        p = w.attached_pane
        p.select_pane()

        # Print the last-in-history command in the pane
        p.cmd("send-keys", " fc -ln -1")
        p.cmd("send-keys", "Enter")

        buffer_name = "test"
        sent_cmd = None

        def f():
            # from v0.7.4 libtmux session.cmd adds target -t self.id by default
            # show-buffer doesn't accept -t, use global cmd.

            # Get the contents of the pane
            p.cmd("capture-pane", "-b", buffer_name)

            captured_pane = session.server.cmd("show-buffer", "-b", buffer_name)
            session.server.cmd("delete-buffer", "-b", buffer_name)

            # Parse the sent and last-in-history commands
            sent_cmd = captured_pane.stdout[0].strip()
            history_cmd = captured_pane.stdout[-2].strip()

            return assertCase(sent_cmd, history_cmd)

        assert retry_until(f), f"Unknown sent command: [{sent_cmd}] in {assertCase}"


def test_session_options(session):
    sconfig = ConfigReader._from_file(
        test_utils.get_config_file("workspacebuilder/session_options.yaml")
    )
    sconfig = config.expand(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig)
    builder.build(session=session)

    assert "/bin/sh" in session.show_option("default-shell")
    assert "/bin/sh" in session.show_option("default-command")


def test_global_options(session):
    sconfig = ConfigReader._from_file(
        test_utils.get_config_file("workspacebuilder/global_options.yaml")
    )
    sconfig = config.expand(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig)
    builder.build(session=session)

    assert "top" in session.show_option("status-position", _global=True)
    assert 493 == session.show_option("repeat-time", _global=True)


def test_global_session_env_options(session, monkeypatch):
    visual_silence = "on"
    monkeypatch.setenv("VISUAL_SILENCE", str(visual_silence))
    repeat_time = 738
    monkeypatch.setenv("REPEAT_TIME", str(repeat_time))
    main_pane_height = 8
    monkeypatch.setenv("MAIN_PANE_HEIGHT", str(main_pane_height))

    sconfig = ConfigReader._from_file(
        test_utils.get_config_file("workspacebuilder/env_var_options.yaml")
    )
    sconfig = config.expand(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig)
    builder.build(session=session)

    assert visual_silence in session.show_option("visual-silence", _global=True)
    assert repeat_time == session.show_option("repeat-time")
    assert main_pane_height == session.attached_window.show_window_option(
        "main-pane-height"
    )


def test_window_options(session):
    sconfig = ConfigReader._from_file(
        test_utils.get_config_file("workspacebuilder/window_options.yaml")
    )
    sconfig = config.expand(sconfig)

    if has_gte_version("2.3"):
        sconfig["windows"][0]["options"]["pane-border-format"] = " #P "

    builder = WorkspaceBuilder(sconf=sconfig)

    window_count = len(session._windows)  # current window count
    assert len(session._windows) == window_count
    for w, wconf in builder.iter_create_windows(session):
        for p in builder.iter_create_panes(w, wconf):
            w.select_layout("tiled")  # fix glitch with pane size
            p = p
            assert len(session._windows) == window_count
        assert isinstance(w, Window)
        assert w.show_window_option("main-pane-height") == 5
        if has_gte_version("2.3"):
            assert w.show_window_option("pane-border-format") == " #P "

        assert len(session._windows) == window_count
        window_count += 1
        w.select_layout(wconf["layout"])


@pytest.mark.flaky(reruns=5)
def test_window_options_after(session):
    sconfig = ConfigReader._from_file(
        test_utils.get_config_file("workspacebuilder/window_options_after.yaml")
    )
    sconfig = config.expand(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig)
    builder.build(session=session)

    def assert_last_line(p, s):
        def f():
            pane_out = p.cmd("capture-pane", "-p", "-J").stdout
            while not pane_out[-1].strip():  # delete trailing lines tmux 1.8
                pane_out.pop()
            return len(pane_out) > 1 and pane_out[-2].strip() == s

        # Print output for easier debugging if assertion fails
        return retry_until(f, raises=False)

    for i, pane in enumerate(session.attached_window.panes):
        assert assert_last_line(
            pane, str(i)
        ), "Initial command did not execute properly/" + str(i)
        pane.cmd("send-keys", "Up")  # Will repeat echo
        pane.enter()  # in each iteration
        assert assert_last_line(
            pane, str(i)
        ), "Repeated command did not execute properly/" + str(i)

    session.cmd("send-keys", " echo moo")
    session.cmd("send-keys", "Enter")

    for pane in session.attached_window.panes:
        assert assert_last_line(
            pane, "moo"
        ), "Synchronized command did not execute properly"


def test_window_shell(session):
    sconfig = ConfigReader._from_file(
        test_utils.get_config_file("workspacebuilder/window_shell.yaml")
    )
    sconfig = config.expand(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig)

    for w, wconf in builder.iter_create_windows(session):
        if "window_shell" in wconf:
            assert wconf["window_shell"] == "top"

        def f():
            session.server._update_windows()
            return w["window_name"] != "top"

        retry_until(f)

        assert w.name != "top"


def test_environment_variables(session):
    sconfig = ConfigReader._from_file(
        test_utils.get_config_file("workspacebuilder/environment_vars.yaml")
    )
    sconfig = config.expand(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig)
    builder.build(session)

    assert session.getenv("FOO") == "BAR"
    assert session.getenv("PATH") == "/tmp"


def test_automatic_rename_option(session):
    """With option automatic-rename: on."""
    sconfig = ConfigReader._from_file(
        test_utils.get_config_file("workspacebuilder/window_automatic_rename.yaml")
    )

    # This should be a command guaranteed to be terminal name across systems
    portable_command = sconfig["windows"][0]["panes"][0]["shell_command"][0]["cmd"]
    # If a command is like "man ls", get the command base name, "ls"
    if " " in portable_command:
        portable_command = portable_command.split(" ")[0]

    builder = WorkspaceBuilder(sconf=sconfig)

    window_count = len(session._windows)  # current window count
    assert len(session._windows) == window_count
    for w, wconf in builder.iter_create_windows(session):

        for p in builder.iter_create_panes(w, wconf):
            w.select_layout("tiled")  # fix glitch with pane size
            p = p
            assert len(session._windows), window_count
        assert isinstance(w, Window)
        assert w.show_window_option("automatic-rename") == "on"

        assert len(session._windows) == window_count

        window_count += 1
        w.select_layout(wconf["layout"])

    assert session.name != "tmuxp"
    w = session.windows[0]

    def check_window_name_mismatch() -> bool:
        session.server._update_windows()
        return w.name != portable_command

    assert retry_until(check_window_name_mismatch, 2, interval=0.25)

    pane_base_index = w.show_window_option("pane-base-index", g=True)
    w.select_pane(pane_base_index)

    def check_window_name_match() -> bool:
        session.server._update_windows()
        return w.name == portable_command

    assert retry_until(
        check_window_name_match, 2, interval=0.25
    ), f"Window name {w.name} should be {portable_command}"

    w.select_pane("-D")

    assert retry_until(check_window_name_mismatch, 2, interval=0.25)


def test_blank_pane_count(session):
    """:todo: Verify blank panes of various types build into workspaces."""
    yaml_config_file = EXAMPLE_PATH / "blank-panes.yaml"
    test_config = ConfigReader._from_file(yaml_config_file)

    test_config = config.expand(test_config)
    builder = WorkspaceBuilder(sconf=test_config)
    builder.build(session=session)

    assert session == builder.session

    window1 = session.find_where({"window_name": "Blank pane test"})
    assert len(window1._panes) == 3

    window2 = session.find_where({"window_name": "More blank panes"})
    assert len(window2._panes) == 3

    window3 = session.find_where({"window_name": "Empty string (return)"})
    assert len(window3._panes) == 3

    window4 = session.find_where({"window_name": "Blank with options"})
    assert len(window4._panes) == 2


def test_start_directory(session, tmp_path: pathlib.Path):
    test_dir = tmp_path / "foo bar"
    test_dir.mkdir()

    yaml_config = test_utils.read_config_file("workspacebuilder/start_directory.yaml")
    test_config = yaml_config.format(TEST_DIR=test_dir)

    sconfig = ConfigReader._load(format="yaml", content=test_config)
    sconfig = config.expand(sconfig)
    sconfig = config.trickle(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig)
    builder.build(session=session)

    assert session == builder.session
    dirs = ["/usr/bin", "/dev", str(test_dir), "/usr", "/usr"]

    for path, window in zip(dirs, session.windows):
        for p in window.panes:

            def f():
                p.server._update_panes()
                pane_path = p.current_path
                return path in pane_path or pane_path == path

            # handle case with OS X adding /private/ to /tmp/ paths
            assert retry_until(f)


def test_start_directory_relative(session, tmp_path: pathlib.Path):
    """Same as above test, but with relative start directory, mimicking
    loading it from a location of project file. Like::

    $ tmuxp load ~/workspace/myproject/.tmuxp.yaml

    instead of::

    $ cd ~/workspace/myproject/.tmuxp.yaml
    $ tmuxp load .

    """
    yaml_config = test_utils.read_config_file(
        "workspacebuilder/start_directory_relative.yaml"
    )

    test_dir = tmp_path / "foo bar"
    test_dir.mkdir()
    config_dir = tmp_path / "testRelConfigDir"
    config_dir.mkdir()

    test_config = yaml_config.format(TEST_DIR=test_dir)
    sconfig = ConfigReader._load(format="yaml", content=test_config)
    # the second argument of os.getcwd() mimics the behavior
    # the CLI loader will do, but it passes in the config file's location.
    sconfig = config.expand(sconfig, config_dir)

    sconfig = config.trickle(sconfig)

    assert os.path.exists(config_dir)
    assert os.path.exists(test_dir)
    builder = WorkspaceBuilder(sconf=sconfig)
    builder.build(session=session)

    assert session == builder.session

    dirs = ["/usr/bin", "/dev", str(test_dir), str(config_dir), str(config_dir)]

    for path, window in zip(dirs, session.windows):
        for p in window.panes:

            def f():
                p.server._update_panes()
                # Handle case where directories resolve to /private/ in OSX
                pane_path = p.current_path
                return path in pane_path or pane_path == path

            assert retry_until(f)


@pytest.mark.skipif(
    has_lt_version("3.2a"), reason="needs format introduced in tmux >= 3.2a"
)
def test_start_directory_sets_session_path(server):
    sconfig = ConfigReader._from_file(
        test_utils.get_config_file("workspacebuilder/start_directory_session_path.yaml")
    )
    sconfig = config.expand(sconfig)
    sconfig = config.trickle(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig, server=server)
    builder.build()

    session = builder.session
    expected = "{0}|/usr".format(session.id)

    cmd = server.cmd("list-sessions", "-F", "#{session_id}|#{session_path}")
    assert expected in cmd.stdout


def test_pane_order(session):
    """Pane ordering based on position in config and ``pane_index``.

    Regression test for https://github.com/tmux-python/tmuxp/issues/15.
    """
    yaml_config = test_utils.read_config_file(
        "workspacebuilder/pane_ordering.yaml"
    ).format(HOME=os.path.realpath(os.path.expanduser("~")))

    # test order of `panes` (and pane_index) above against pane_dirs
    pane_paths = [
        "/usr/bin",
        "/usr",
        "/etc",
        os.path.realpath(os.path.expanduser("~")),
    ]

    sconfig = ConfigReader._load(format="yaml", content=yaml_config)
    sconfig = config.expand(sconfig)
    sconfig = config.trickle(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig)

    window_count = len(session._windows)  # current window count
    assert len(session._windows) == window_count

    for w, wconf in builder.iter_create_windows(session):
        for p in builder.iter_create_panes(w, wconf):
            w.select_layout("tiled")  # fix glitch with pane size
            assert len(session._windows) == window_count

        assert isinstance(w, Window)

        assert len(session._windows) == window_count
        window_count += 1

    for w in session.windows:
        pane_base_index = w.show_window_option("pane-base-index", g=True)
        for p_index, p in enumerate(w.list_panes(), start=pane_base_index):
            assert int(p_index) == int(p.index)

            # pane-base-index start at base-index, pane_paths always start
            # at 0 since python list.
            pane_path = pane_paths[p_index - pane_base_index]

            def f():
                p.server._update_panes()
                return p.current_path == pane_path

            assert retry_until(f)


def test_window_index(session):
    proc = session.cmd("show-option", "-gv", "base-index")
    base_index = int(proc.stdout[0])
    name_index_map = {"zero": 0 + base_index, "one": 1 + base_index, "five": 5}

    sconfig = ConfigReader._from_file(
        test_utils.get_config_file("workspacebuilder/window_index.yaml")
    )
    sconfig = config.expand(sconfig)
    sconfig = config.trickle(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig)

    for window, _ in builder.iter_create_windows(session):
        expected_index = name_index_map[window["window_name"]]
        assert int(window["window_index"]) == expected_index


def test_before_load_throw_error_if_retcode_error(server):
    config_script_fails = test_utils.read_config_file(
        "workspacebuilder/config_script_fails.yaml"
    )
    yaml_config = config_script_fails.format(
        script_failed=FIXTURE_PATH / "script_failed.sh",
    )

    sconfig = ConfigReader._load(format="yaml", content=yaml_config)
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
    config_script_not_exists = test_utils.read_config_file(
        "workspacebuilder/config_script_not_exists.yaml"
    )
    yaml_config = config_script_not_exists.format(
        script_not_exists=FIXTURE_PATH / "script_not_exists.sh",
    )
    sconfig = ConfigReader._load(format="yaml", content=yaml_config)
    sconfig = config.expand(sconfig)
    sconfig = config.trickle(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig)

    with temp_session(server) as session:
        session_name = session.name
        temp_session_exists = server.has_session(session.name)
        assert temp_session_exists
        with pytest.raises((exc.BeforeLoadScriptNotExists, OSError)) as excinfo:
            builder.build(session=session)
            excinfo.match(r"No such file or directory")
        result = server.has_session(session_name)
        assert not result, "Kills session if before_script doesn't exist"


def test_before_load_true_if_test_passes(server):
    config_script_completes = test_utils.read_config_file(
        "workspacebuilder/config_script_completes.yaml"
    )
    script_complete_sh = FIXTURE_PATH / "script_complete.sh"
    assert script_complete_sh.exists()

    yaml_config = config_script_completes.format(script_complete=script_complete_sh)
    sconfig = ConfigReader._load(format="yaml", content=yaml_config)
    sconfig = config.expand(sconfig)
    sconfig = config.trickle(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig)

    with temp_session(server) as session:
        builder.build(session=session)


def test_before_load_true_if_test_passes_with_args(server):
    config_script_completes = test_utils.read_config_file(
        "workspacebuilder/config_script_completes.yaml"
    )
    script_complete_sh = FIXTURE_PATH / "script_complete.sh"
    assert script_complete_sh.exists()

    yaml_config = config_script_completes.format(script_complete=script_complete_sh)

    sconfig = ConfigReader._load(format="yaml", content=yaml_config)
    sconfig = config.expand(sconfig)
    sconfig = config.trickle(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig)

    with temp_session(server) as session:
        builder.build(session=session)


def test_plugin_system_before_workspace_builder(
    monkeypatch_plugin_test_packages, session
):
    sconfig = ConfigReader._from_file(
        path=test_utils.get_config_file("workspacebuilder/plugin_bwb.yaml")
    )
    sconfig = config.expand(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig, plugins=load_plugins(sconfig))
    assert len(builder.plugins) > 0

    builder.build(session=session)

    proc = session.cmd("display-message", "-p", "'#S'")
    assert proc.stdout[0] == "'plugin_test_bwb'"


def test_plugin_system_on_window_create(monkeypatch_plugin_test_packages, session):
    sconfig = ConfigReader._from_file(
        path=test_utils.get_config_file("workspacebuilder/plugin_owc.yaml")
    )
    sconfig = config.expand(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig, plugins=load_plugins(sconfig))
    assert len(builder.plugins) > 0

    builder.build(session=session)

    proc = session.cmd("display-message", "-p", "'#W'")
    assert proc.stdout[0] == "'plugin_test_owc'"


def test_plugin_system_after_window_finished(monkeypatch_plugin_test_packages, session):
    sconfig = ConfigReader._from_file(
        path=test_utils.get_config_file("workspacebuilder/plugin_awf.yaml")
    )
    sconfig = config.expand(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig, plugins=load_plugins(sconfig))
    assert len(builder.plugins) > 0

    builder.build(session=session)

    proc = session.cmd("display-message", "-p", "'#W'")
    assert proc.stdout[0] == "'plugin_test_awf'"


def test_plugin_system_on_window_create_multiple_windows(session):
    sconfig = ConfigReader._from_file(
        path=test_utils.get_config_file(
            "workspacebuilder/plugin_owc_multiple_windows.yaml"
        )
    )
    sconfig = config.expand(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig, plugins=load_plugins(sconfig))
    assert len(builder.plugins) > 0

    builder.build(session=session)

    proc = session.cmd("list-windows", "-F", "'#W'")
    assert "'plugin_test_owc_mw'" in proc.stdout
    assert "'plugin_test_owc_mw_2'" in proc.stdout


def test_plugin_system_after_window_finished_multiple_windows(
    monkeypatch_plugin_test_packages, session
):
    sconfig = ConfigReader._from_file(
        path=test_utils.get_config_file(
            "workspacebuilder/plugin_awf_multiple_windows.yaml"
        )
    )
    sconfig = config.expand(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig, plugins=load_plugins(sconfig))
    assert len(builder.plugins) > 0

    builder.build(session=session)

    proc = session.cmd("list-windows", "-F", "'#W'")
    assert "'plugin_test_awf_mw'" in proc.stdout
    assert "'plugin_test_awf_mw_2'" in proc.stdout


def test_plugin_system_multiple_plugins(monkeypatch_plugin_test_packages, session):
    sconfig = ConfigReader._from_file(
        path=test_utils.get_config_file("workspacebuilder/plugin_multiple_plugins.yaml")
    )
    sconfig = config.expand(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig, plugins=load_plugins(sconfig))
    assert len(builder.plugins) > 0

    builder.build(session=session)

    # Drop through to the before_script plugin hook
    proc = session.cmd("display-message", "-p", "'#S'")
    assert proc.stdout[0] == "'plugin_test_bwb'"

    # Drop through to the after_window_finished. This won't succeed
    # unless on_window_create succeeds because of how the test plugin
    # override methods are currently written
    proc = session.cmd("display-message", "-p", "'#W'")
    assert proc.stdout[0] == "'mp_test_awf'"


def test_load_configs_same_session(server):
    sconfig = ConfigReader._from_file(
        path=test_utils.get_config_file("workspacebuilder/three_windows.yaml")
    )

    builder = WorkspaceBuilder(sconf=sconfig, server=server)
    builder.build()

    assert len(server.sessions) == 1
    assert len(server.sessions[0]._windows) == 3

    sconfig = ConfigReader._from_file(
        path=test_utils.get_config_file("workspacebuilder/two_windows.yaml")
    )

    builder = WorkspaceBuilder(sconf=sconfig, server=server)
    builder.build()
    assert len(server.sessions) == 2
    assert len(server.sessions[1]._windows) == 2

    sconfig = ConfigReader._from_file(
        path=test_utils.get_config_file("workspacebuilder/two_windows.yaml")
    )

    builder = WorkspaceBuilder(sconf=sconfig, server=server)
    builder.build(server.sessions[1], True)

    assert len(server.sessions) == 2
    assert len(server.sessions[1]._windows) == 4


def test_load_configs_separate_sessions(server):
    sconfig = ConfigReader._from_file(
        path=test_utils.get_config_file("workspacebuilder/three_windows.yaml")
    )

    builder = WorkspaceBuilder(sconf=sconfig, server=server)
    builder.build()

    assert len(server.sessions) == 1
    assert len(server.sessions[0]._windows) == 3

    sconfig = ConfigReader._from_file(
        path=test_utils.get_config_file("workspacebuilder/two_windows.yaml")
    )

    builder = WorkspaceBuilder(sconf=sconfig, server=server)
    builder.build()

    assert len(server.sessions) == 2
    assert len(server.sessions[0]._windows) == 3
    assert len(server.sessions[1]._windows) == 2


def test_find_current_active_pane(server, monkeypatch):
    sconfig = ConfigReader._from_file(
        path=test_utils.get_config_file("workspacebuilder/three_windows.yaml")
    )

    builder = WorkspaceBuilder(sconf=sconfig, server=server)
    builder.build()

    sconfig = ConfigReader._from_file(
        path=test_utils.get_config_file("workspacebuilder/two_windows.yaml")
    )

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


@pytest.mark.parametrize(
    "yaml,output,should_see",
    [
        [
            textwrap.dedent(
                """
session_name: Should not execute
windows:
- panes:
  - shell_command: echo "___$((1 + 3))___"
    enter: false
    """
            ),
            "___4___",
            False,
        ],
        [
            textwrap.dedent(
                """
session_name: Should not execute
windows:
- panes:
  - shell_command:
    - echo "___$((1 + 3))___"
    enter: false
    """
            ),
            "___4___",
            False,
        ],
        [
            textwrap.dedent(
                """
session_name: Should execute
windows:
- panes:
  - shell_command: echo "___$((1 + 3))___"
  """
            ),
            "___4___",
            True,
        ],
        [
            textwrap.dedent(
                """
session_name: Should execute
windows:
- panes:
  - shell_command:
    - echo "___$((1 + 3))___"
  """
            ),
            "___4___",
            True,
        ],
        [
            textwrap.dedent(
                """
session_name: Should not execute
windows:
- panes:
  - shell_command:
    - cmd: echo "___$((1 + 3))___"
      enter: false
    """
            ),
            "___4___",
            False,
        ],
        [
            textwrap.dedent(
                """
session_name: Should not execute
windows:
- panes:
  - shell_command:
    - cmd: echo "___$((1 + 3))___"
      enter: false
    """
            ),
            "___4___",
            False,
        ],
        [
            textwrap.dedent(
                """
session_name: Should execute
windows:
- panes:
  - shell_command: echo "___$((1 + 3))___"
  """
            ),
            "___4___",
            True,
        ],
        [
            textwrap.dedent(
                """
session_name: Should execute
windows:
- panes:
  - shell_command:
    - cmd: echo "other command"
    - cmd: echo "___$((1 + 3))___"
  """
            ),
            "___4___",
            True,
        ],
    ],
    ids=[
        "pane_enter_false_shortform",
        "pane_enter_false_longform",
        "pane_enter_default_shortform",
        "pane_enter_default_longform",
        "pane_command_enter_false_shortform",
        "pane_command_enter_false_longform",
        "pane_command_enter_default_shortform",
        "pane_command_enter_default_longform",
    ],
)
def test_load_workspace_enter(
    tmp_path: pathlib.Path,
    server: libtmux.Server,
    monkeypatch: pytest.MonkeyPatch,
    yaml,
    output,
    should_see,
):
    yaml_config = tmp_path / "simple.yaml"
    yaml_config.write_text(yaml, encoding="utf-8")
    sconfig = ConfigReader._from_file(yaml_config)
    sconfig = config.expand(sconfig)
    sconfig = config.trickle(sconfig)
    builder = WorkspaceBuilder(sconf=sconfig, server=server)
    builder.build()

    session = builder.session
    pane = session.attached_pane

    def fn():
        captured_pane = "\n".join(pane.capture_pane())

        if should_see:
            return output in captured_pane
        else:
            return output not in captured_pane

    assert retry_until(
        fn, 1
    ), f'Should{" " if should_see else "not "} output in captured pane'


@pytest.mark.parametrize(
    "yaml,sleep,output",
    [
        [
            textwrap.dedent(
                """
session_name: Should not execute
windows:
- panes:
  - shell_command:
    - cmd: echo "___$((1 + 5))___"
      sleep_before: .15
    - cmd: echo "___$((1 + 3))___"
      sleep_before: .35
    """
            ),
            0.5,
            "___4___",
        ],
        [
            textwrap.dedent(
                """
session_name: Should not execute
windows:
- panes:
  - shell_command:
    - cmd: echo "___$((1 + 5))___"
      sleep_before: 1
    - cmd: echo "___$((1 + 3))___"
      sleep_before: .25
    """
            ),
            1.25,
            "___4___",
        ],
        [
            textwrap.dedent(
                """
session_name: Should not execute
windows:
- panes:
  - shell_command:
    - cmd: echo "___$((1 + 3))___"
    sleep_before: .5
    """
            ),
            0.5,
            "___4___",
        ],
        [
            textwrap.dedent(
                """
session_name: Should not execute
windows:
- panes:
  - shell_command:
    - cmd: echo "___$((1 + 3))___"
    sleep_before: 1
    """
            ),
            1,
            "___4___",
        ],
        [
            textwrap.dedent(
                """
session_name: Should not execute
shell_command_before:
  - cmd: echo "sleeping before"
    sleep_before: .5
windows:
- panes:
  - echo "___$((1 + 3))___"
    """
            ),
            0.5,
            "___4___",
        ],
    ],
    ids=[
        "command_level_sleep_shortform",
        "command_level_pane_sleep_longform",
        "pane_sleep_shortform",
        "pane_sleep_longform",
        "shell_before_before_command_level",
    ],
)
@pytest.mark.flaky(reruns=3)
def test_load_workspace_sleep(
    tmp_path: pathlib.Path,
    server: libtmux.Server,
    monkeypatch: pytest.MonkeyPatch,
    yaml,
    sleep: int,
    output,
):
    yaml_config = tmp_path / "simple.yaml"
    yaml_config.write_text(yaml, encoding="utf-8")
    sconfig = ConfigReader._from_file(yaml_config)
    sconfig = config.expand(sconfig)
    sconfig = config.trickle(sconfig)
    builder = WorkspaceBuilder(sconf=sconfig, server=server)

    t = time.process_time()

    builder.build()
    time.sleep(0.5)
    session = builder.session
    pane = session.attached_pane

    while (time.process_time() - t) * 1000 < sleep:
        captured_pane = "\n".join(pane.capture_pane())

        assert output not in captured_pane
        time.sleep(0.1)
    captured_pane = "\n".join(pane.capture_pane())
    assert output in captured_pane


def test_first_pane_start_directory(session, tmp_path: pathlib.Path):
    yaml_config = test_utils.get_config_file(
        "workspacebuilder/first_pane_start_directory.yaml"
    )

    sconfig = ConfigReader._from_file(yaml_config)
    sconfig = config.expand(sconfig)
    sconfig = config.trickle(sconfig)

    builder = WorkspaceBuilder(sconf=sconfig)
    builder.build(session=session)

    assert session == builder.session
    dirs = ["/usr", "/etc"]

    assert session.windows
    window = session.windows[0]
    for path, p in zip(dirs, window.panes):

        def f():
            p.server._update_panes()
            pane_path = p.current_path
            return path in pane_path or pane_path == path

        # handle case with OS X adding /private/ to /tmp/ paths
        assert retry_until(f)


@pytest.mark.skipif(
    has_lt_version("2.9"), reason="needs option introduced in tmux >= 2.9"
)
def test_layout_main_horizontal(session):
    yaml_config = test_utils.get_config_file("workspacebuilder/three_pane.yaml")
    sconfig = ConfigReader._from_file(path=yaml_config)

    builder = WorkspaceBuilder(sconf=sconfig)
    builder.build(session=session)

    assert session.windows
    window = session.windows[0]

    assert len(window.panes) == 3
    main_horizontal_pane, *panes = window.panes

    def height(p):
        return int(p._info["pane_height"])

    def width(p):
        return int(p._info["pane_width"])

    main_horizontal_pane_height = height(main_horizontal_pane)
    pane_heights = [height(pane) for pane in panes]
    # TODO: When libtmux has new pane formatters added, use that to detect top / bottom
    assert all(
        main_horizontal_pane_height != pane_height for pane_height in pane_heights
    ), "The top row should not be the same size as the bottom row (even though it can)"
    assert all(
        pane_heights[0] == pane_height for pane_height in pane_heights
    ), "The bottom row should be uniform height"
    assert width(main_horizontal_pane) > width(panes[0])

    def is_almost_equal(x, y):
        return abs(x - y) <= 1

    assert is_almost_equal(height(panes[0]), height(panes[1]))
    assert is_almost_equal(width(panes[0]), width(panes[1]))


class DefaultSizeNamespaceFixture(t.NamedTuple):
    test_id: str
    TMUXP_DEFAULT_SIZE: t.Optional[str]
    raises: bool
    confoverrides: t.Dict[str, t.Any]


DEFAULT_SIZE_FIXTURES = [
    DefaultSizeNamespaceFixture(
        test_id="default-behavior",
        TMUXP_DEFAULT_SIZE=None,
        raises=False,
        confoverrides={},
    ),
    DefaultSizeNamespaceFixture(
        test_id="v1.13.1 default-size-breaks",
        TMUXP_DEFAULT_SIZE=None,
        raises=True,
        confoverrides={"options": {"default-size": "80x24"}},
    ),
    DefaultSizeNamespaceFixture(
        test_id="v1.13.1-option-workaround",
        TMUXP_DEFAULT_SIZE=None,
        raises=False,
        confoverrides={"options": {"default-size": "800x600"}},
    ),
]


@pytest.mark.parametrize(
    DefaultSizeNamespaceFixture._fields,
    DEFAULT_SIZE_FIXTURES,
    ids=[f.test_id for f in DEFAULT_SIZE_FIXTURES],
)
@pytest.mark.skipif(has_lt_version("2.9"), reason="default-size only applies there")
def test_issue_800_default_size_many_windows(
    server: "Server",
    monkeypatch: pytest.MonkeyPatch,
    test_id: str,
    TMUXP_DEFAULT_SIZE: t.Optional[str],
    raises: bool,
    confoverrides: t.Dict[str, t.Any],
) -> None:
    """Recreate default-size issue.

    v1.13.1 added a default-size, but this can break building workspaces with
    a lot of panes.

    See also: https://github.com/tmux-python/tmuxp/issues/800
    """
    yaml_config = test_utils.get_config_file(
        "regressions/issue_800_default_size_many_windows.yaml"
    )

    sconfig = ConfigReader._from_file(yaml_config)
    sconfig = config.expand(sconfig)
    sconfig = config.trickle(sconfig)

    if isinstance(confoverrides, dict):
        for k, v in confoverrides.items():
            sconfig[k] = v

    if TMUXP_DEFAULT_SIZE is not None:
        monkeypatch.setenv("TMUXP_DEFAULT_SIZE", TMUXP_DEFAULT_SIZE)

    builder = WorkspaceBuilder(sconf=sconfig, server=server)

    if raises:
        with pytest.raises(Exception):
            builder.build()

        builder.session.kill_session()

        with pytest.raises(libtmux.exc.LibTmuxException, match="no space for new pane"):
            builder.build()
        return

    builder.build()
    assert len(server.list_sessions()) == 1
