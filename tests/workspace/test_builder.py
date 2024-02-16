"""Test for tmuxp workspace builder."""
import functools
import os
import pathlib
import textwrap
import time
import typing as t

import libtmux
import pytest
from libtmux._internal.query_list import ObjectDoesNotExist
from libtmux.common import has_gte_version, has_lt_version
from libtmux.exc import LibTmuxException
from libtmux.pane import Pane
from libtmux.server import Server
from libtmux.session import Session
from libtmux.test import retry_until, temp_session
from libtmux.window import Window

from tmuxp import exc
from tmuxp._internal.config_reader import ConfigReader
from tmuxp.cli.load import load_plugins
from tmuxp.workspace import loader
from tmuxp.workspace.builder import WorkspaceBuilder

from ..constants import EXAMPLE_PATH, FIXTURE_PATH
from ..fixtures import utils as test_utils

if t.TYPE_CHECKING:

    class AssertCallbackProtocol(t.Protocol):
        """Assertion callback type protocol."""

        def __call__(self, cmd: str, hist: str) -> bool:
            """Run function code for testing assertion."""
            ...


def test_split_windows(session: Session) -> None:
    """Test workspace builder splits windows in a tmux session."""
    workspace = ConfigReader._from_file(
        test_utils.get_workspace_file("workspace/builder/two_pane.yaml"),
    )

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)

    window_count = len(session.windows)  # current window count
    assert len(session.windows) == window_count
    for w, wconf in builder.iter_create_windows(session):
        for p in builder.iter_create_panes(w, wconf):
            w.select_layout("tiled")  # fix glitch with pane size
            p = p
            assert len(session.windows) == window_count
        assert isinstance(w, Window)

        assert len(session.windows) == window_count
        window_count += 1


def test_split_windows_three_pane(session: Session) -> None:
    """Test workspace builder splits windows in a tmux session."""
    workspace = ConfigReader._from_file(
        test_utils.get_workspace_file("workspace/builder/three_pane.yaml"),
    )

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)

    window_count = len(session.windows)  # current window count
    assert len(session.windows) == window_count
    for w, wconf in builder.iter_create_windows(session):
        for p in builder.iter_create_panes(w, wconf):
            w.select_layout("tiled")  # fix glitch with pane size
            p = p
            assert len(session.windows) == window_count
        assert isinstance(w, Window)

        assert len(session.windows) == window_count
        window_count += 1
        w.set_window_option("main-pane-height", 50)
        w.select_layout(wconf["layout"])


def test_focus_pane_index(session: Session) -> None:
    """Test focus of pane by index works correctly, including with pane-base-index."""
    workspace = ConfigReader._from_file(
        test_utils.get_workspace_file("workspace/builder/focus_and_pane.yaml"),
    )
    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)

    builder.build(session=session)

    assert session.attached_window.name == "focused window"

    _pane_base_index = session.attached_window.show_window_option(
        "pane-base-index",
        g=True,
    )
    assert isinstance(_pane_base_index, int)
    pane_base_index = int(_pane_base_index)

    pane_base_index = 0 if not pane_base_index else int(pane_base_index)

    # get the pane index for each pane
    pane_base_indexes = [
        int(pane.index)
        for pane in session.attached_window.panes
        if pane is not None and pane.index is not None
    ]

    pane_indexes_should_be = [pane_base_index + x for x in range(0, 3)]
    assert pane_indexes_should_be == pane_base_indexes

    w = session.attached_window

    assert w.name != "man"

    pane_path = "/usr"
    p = None

    def f_check() -> bool:
        nonlocal p
        p = w.attached_pane
        assert p is not None
        return p.pane_current_path == pane_path

    assert retry_until(f_check)

    assert p is not None
    assert p.pane_current_path == pane_path

    proc = session.cmd("show-option", "-gv", "base-index")
    base_index = int(proc.stdout[0])

    window3 = session.windows.get(window_index=str(base_index + 2))
    assert isinstance(window3, Window)

    p = None
    pane_path = "/"

    def f_check_again() -> bool:
        nonlocal p
        p = window3.attached_pane
        assert p is not None
        return p.pane_current_path == pane_path

    assert retry_until(f_check_again)

    assert p is not None
    assert p.pane_current_path is not None
    assert isinstance(p.pane_current_path, str)
    assert p.pane_current_path == pane_path


@pytest.mark.skip(
    reason="""
Test needs to be rewritten, assertion not reliable across platforms
and CI. See https://github.com/tmux-python/tmuxp/issues/310.
    """.strip(),
)
def test_suppress_history(session: Session) -> None:
    """Test suppression of command history."""
    workspace = ConfigReader._from_file(
        test_utils.get_workspace_file("workspace/builder/suppress_history.yaml"),
    )
    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    builder.build(session=session)

    inHistoryWindow = session.windows.get(window_name="inHistory")
    assert inHistoryWindow is not None
    isMissingWindow = session.windows.get(window_name="isMissing")
    assert isMissingWindow is not None

    def assertHistory(cmd: str, hist: str) -> bool:
        return "inHistory" in cmd and cmd.endswith(hist)

    def assertIsMissing(cmd: str, hist: str) -> bool:
        return "isMissing" in cmd and not cmd.endswith(hist)

    for w, window_name, assertCase in [
        (inHistoryWindow, "inHistory", assertHistory),
        (isMissingWindow, "isMissing", assertIsMissing),
    ]:
        assert w.name == window_name
        w.select()
        p = w.attached_pane
        assert p is not None
        p.select()

        # Print the last-in-history command in the pane
        p.cmd("send-keys", " fc -ln -1")
        p.cmd("send-keys", "Enter")

        buffer_name = "test"
        sent_cmd = None

        def f(p: Pane, buffer_name: str, assertCase: AssertCallbackProtocol) -> bool:
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

        _f = functools.partial(f, p=p, buffer_name=buffer_name, assertCase=assertCase)

        assert retry_until(_f), f"Unknown sent command: [{sent_cmd}] in {assertCase}"


def test_session_options(session: Session) -> None:
    """Test setting of options to session scope."""
    workspace = ConfigReader._from_file(
        test_utils.get_workspace_file("workspace/builder/session_options.yaml"),
    )
    workspace = loader.expand(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    builder.build(session=session)

    _default_shell = session.show_option("default-shell")
    assert isinstance(_default_shell, str)
    assert "/bin/sh" in _default_shell

    _default_command = session.show_option("default-command")
    assert isinstance(_default_command, str)
    assert "/bin/sh" in _default_command


def test_global_options(session: Session) -> None:
    """Test setting of global options."""
    workspace = ConfigReader._from_file(
        test_utils.get_workspace_file("workspace/builder/global_options.yaml"),
    )
    workspace = loader.expand(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    builder.build(session=session)

    _status_position = session.show_option("status-position", _global=True)
    assert isinstance(_status_position, str)
    assert "top" in _status_position
    assert session.show_option("repeat-time", _global=True) == 493


def test_global_session_env_options(
    session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test setting of global option variables."""
    visual_silence = "on"
    monkeypatch.setenv("VISUAL_SILENCE", str(visual_silence))
    repeat_time = 738
    monkeypatch.setenv("REPEAT_TIME", str(repeat_time))
    main_pane_height = 8
    monkeypatch.setenv("MAIN_PANE_HEIGHT", str(main_pane_height))

    workspace = ConfigReader._from_file(
        test_utils.get_workspace_file("workspace/builder/env_var_options.yaml"),
    )
    workspace = loader.expand(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    builder.build(session=session)

    _visual_silence = session.show_option("visual-silence", _global=True)
    assert isinstance(_visual_silence, str)
    assert visual_silence in _visual_silence
    assert repeat_time == session.show_option("repeat-time")
    assert main_pane_height == session.attached_window.show_window_option(
        "main-pane-height",
    )


def test_window_options(
    session: Session,
) -> None:
    """Test setting of window options."""
    workspace = ConfigReader._from_file(
        test_utils.get_workspace_file("workspace/builder/window_options.yaml"),
    )
    workspace = loader.expand(workspace)

    if has_gte_version("2.3"):
        workspace["windows"][0]["options"]["pane-border-format"] = " #P "

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)

    window_count = len(session.windows)  # current window count
    assert len(session.windows) == window_count
    for w, wconf in builder.iter_create_windows(session):
        for p in builder.iter_create_panes(w, wconf):
            w.select_layout("tiled")  # fix glitch with pane size
            p = p
            assert len(session.windows) == window_count
        assert isinstance(w, Window)
        assert w.show_window_option("main-pane-height") == 5
        if has_gte_version("2.3"):
            assert w.show_window_option("pane-border-format") == " #P "

        assert len(session.windows) == window_count
        window_count += 1
        w.select_layout(wconf["layout"])


@pytest.mark.flaky(reruns=5)
def test_window_options_after(
    session: Session,
) -> None:
    """Test setting window options via options_after (WorkspaceBuilder.after_window)."""
    workspace = ConfigReader._from_file(
        test_utils.get_workspace_file("workspace/builder/window_options_after.yaml"),
    )
    workspace = loader.expand(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    builder.build(session=session)

    def assert_last_line(p: Pane, s: str) -> bool:
        def f() -> bool:
            pane_out = p.cmd("capture-pane", "-p", "-J").stdout
            while not pane_out[-1].strip():  # delete trailing lines tmux 1.8
                pane_out.pop()
            return len(pane_out) > 1 and pane_out[-2].strip() == s

        # Print output for easier debugging if assertion fails
        return retry_until(f, raises=False)

    for i, pane in enumerate(session.attached_window.panes):
        assert assert_last_line(pane, str(i)), (
            "Initial command did not execute properly/" + str(i)
        )
        pane.cmd("send-keys", "Up")  # Will repeat echo
        pane.enter()  # in each iteration
        assert assert_last_line(pane, str(i)), (
            "Repeated command did not execute properly/" + str(i)
        )

    session.cmd("send-keys", " echo moo")
    session.cmd("send-keys", "Enter")

    for pane in session.attached_window.panes:
        assert assert_last_line(
            pane,
            "moo",
        ), "Synchronized command did not execute properly"


def test_window_shell(
    session: Session,
) -> None:
    """Test execution of commands via tmuxp configuration."""
    workspace = ConfigReader._from_file(
        test_utils.get_workspace_file("workspace/builder/window_shell.yaml"),
    )
    workspace = loader.expand(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)

    for w, wconf in builder.iter_create_windows(session):
        if "window_shell" in wconf:
            assert wconf["window_shell"] == "top"

        def f(w: Window) -> bool:
            return w.window_name != "top"

        _f = functools.partial(f, w=w)

        retry_until(_f)

        assert w.name != "top"


@pytest.mark.skipif(
    has_lt_version("3.0"),
    reason="needs -e flag for new-window and split-window introduced in tmux 3.0",
)
def test_environment_variables(
    session: Session,
) -> None:
    """Test setting of environmental variables in tmux via workspace builder."""
    workspace = ConfigReader._from_file(
        test_utils.get_workspace_file("workspace/builder/environment_vars.yaml"),
    )
    workspace = loader.expand(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    builder.build(session)
    # Give slow shells some time to settle as otherwise tests might fail.
    time.sleep(0.3)

    assert session.getenv("FOO") == "SESSION"
    assert session.getenv("PATH") == "/tmp"

    no_overrides_win = session.windows[0]
    pane = no_overrides_win.panes[0]
    pane.send_keys("echo $FOO")
    assert pane.capture_pane()[1] == "SESSION"

    window_overrides_win = session.windows[1]
    pane = window_overrides_win.panes[0]
    pane.send_keys("echo $FOO")
    assert pane.capture_pane()[1] == "WINDOW"

    pane_overrides_win = session.windows[2]
    pane = pane_overrides_win.panes[0]
    pane.send_keys("echo $FOO")
    assert pane.capture_pane()[1] == "PANE"

    both_overrides_win = session.windows[3]
    pane = both_overrides_win.panes[0]
    pane.send_keys("echo $FOO")
    assert pane.capture_pane()[1] == "WINDOW"
    pane = both_overrides_win.panes[1]
    pane.send_keys("echo $FOO")
    assert pane.capture_pane()[1] == "PANE"


@pytest.mark.skipif(
    has_gte_version("3.0"),
    reason="warnings are not needed for tmux >= 3.0",
)
def test_environment_variables_warns_prior_to_tmux_3_0(
    session: Session,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Warns when environmental variables cannot be set prior to tmux 3.0."""
    workspace = ConfigReader._from_file(
        test_utils.get_workspace_file("workspace/builder/environment_vars.yaml"),
    )
    workspace = loader.expand(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    builder.build(session)

    # environment on sessions should work as this is done using set-environment
    # on the session itself
    assert session.getenv("FOO") == "SESSION"
    assert session.getenv("PATH") == "/tmp"

    assert (
        sum(
            1
            for record in caplog.records
            if "Cannot set environment for new windows." in record.msg
        )
        # From window_overrides and both_overrides, but not
        # both_overrides_in_first_pane.
        == 2
    ), "Warning on creating windows missing"
    assert (
        sum(
            1
            for record in caplog.records
            if "Cannot set environment for new panes." in record.msg
        )
        # From pane_overrides and both_overrides, but not both_overrides_in_first_pane.
        == 2
    ), "Warning on creating panes missing"
    assert (
        sum(
            1
            for record in caplog.records
            if "Cannot set environment for new panes and windows." in record.msg
        )
        # From both_overrides_in_first_pane.
        == 1
    )


def test_automatic_rename_option(
    server: "Server",
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test workspace builder with automatic renaming enabled."""
    monkeypatch.setenv("DISABLE_AUTO_TITLE", "true")
    workspace = ConfigReader._from_file(
        test_utils.get_workspace_file("workspace/builder/window_automatic_rename.yaml"),
    )

    # This should be a command guaranteed to be terminal name across systems
    portable_command = workspace["windows"][0]["panes"][0]["shell_command"][0]["cmd"]
    # If a command is like "man ls", get the command base name, "ls"
    if " " in portable_command:
        portable_command = portable_command.split(" ")[0]

    builder = WorkspaceBuilder(session_config=workspace, server=server)
    builder.build()
    assert builder.session is not None
    session: Session = builder.session
    w: Window = session.windows[0]
    assert len(session.windows) == 1

    assert w.name != "renamed_window"

    def check_window_name_mismatch() -> bool:
        return bool(w.name != portable_command)

    assert retry_until(check_window_name_mismatch, 5, interval=0.25)

    def check_window_name_match() -> bool:
        assert w.show_window_option("automatic-rename") == "on"
        return (
            w.name == pathlib.Path(os.getenv("SHELL", "bash")).name
            or w.name == portable_command
        )

    assert retry_until(
        check_window_name_match,
        4,
        interval=0.05,
    ), f"Window name {w.name} should be {portable_command}"

    w.select_pane("-D")

    assert retry_until(check_window_name_mismatch, 2, interval=0.25)


def test_blank_pane_spawn(
    session: Session,
) -> None:
    """Test various ways of spawning blank panes from a tmuxp configuration.

    :todo: Verify blank panes of various types build into workspaces.
    """
    yaml_workspace_file = EXAMPLE_PATH / "blank-panes.yaml"
    test_config = ConfigReader._from_file(yaml_workspace_file)

    test_config = loader.expand(test_config)
    builder = WorkspaceBuilder(session_config=test_config, server=session.server)
    builder.build(session=session)

    assert session == builder.session

    window1 = session.windows.get(window_name="Blank pane test")
    assert window1 is not None
    assert len(window1.panes) == 3

    window2 = session.windows.get(window_name="More blank panes")
    assert window2 is not None
    assert len(window2.panes) == 3

    window3 = session.windows.get(window_name="Empty string (return)")
    assert window3 is not None
    assert len(window3.panes) == 3

    window4 = session.windows.get(window_name="Blank with options")
    assert window4 is not None
    assert len(window4.panes) == 2


def test_start_directory(session: Session, tmp_path: pathlib.Path) -> None:
    """Test workspace builder setting start_directory relative to current directory."""
    test_dir = tmp_path / "foo bar"
    test_dir.mkdir()

    yaml_workspace = test_utils.read_workspace_file(
        "workspace/builder/start_directory.yaml",
    )
    test_config = yaml_workspace.format(TEST_DIR=test_dir)

    workspace = ConfigReader._load(fmt="yaml", content=test_config)
    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    builder.build(session=session)

    assert session == builder.session
    dirs = ["/usr/bin", "/dev", str(test_dir), "/usr", "/usr"]

    for path, window in zip(dirs, session.windows):
        for p in window.panes:

            def f(path: str, p: Pane) -> bool:
                pane_path = p.pane_current_path
                return (
                    pane_path is not None and path in pane_path
                ) or pane_path == path

            _f = functools.partial(f, path=path, p=p)

            # handle case with OS X adding /private/ to /tmp/ paths
            assert retry_until(_f)


def test_start_directory_relative(session: Session, tmp_path: pathlib.Path) -> None:
    """Test workspace builder setting start_directory relative to project file.

    Same as above test, but with relative start directory, mimicking
    loading it from a location of project file. Like::

        $ tmuxp load ~/workspace/myproject/.tmuxp.yaml

    instead of::

        $ cd ~/workspace/myproject/.tmuxp.yaml
        $ tmuxp load .

    """
    yaml_workspace = test_utils.read_workspace_file(
        "workspace/builder/start_directory_relative.yaml",
    )

    test_dir = tmp_path / "foo bar"
    test_dir.mkdir()
    config_dir = tmp_path / "testRelConfigDir"
    config_dir.mkdir()

    test_config = yaml_workspace.format(TEST_DIR=test_dir)
    workspace = ConfigReader._load(fmt="yaml", content=test_config)
    # the second argument of os.getcwd() mimics the behavior
    # the CLI loader will do, but it passes in the workspace file's location.
    workspace = loader.expand(workspace, config_dir)

    workspace = loader.trickle(workspace)

    assert config_dir.exists()
    assert test_dir.exists()
    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    builder.build(session=session)

    assert session == builder.session

    dirs = ["/usr/bin", "/dev", str(test_dir), str(config_dir), str(config_dir)]

    for path, window in zip(dirs, session.windows):
        for p in window.panes:

            def f(path: str, p: Pane) -> bool:
                pane_path = p.pane_current_path
                return (
                    pane_path is not None and path in pane_path
                ) or pane_path == path

            _f = functools.partial(f, path=path, p=p)

            # handle case with OS X adding /private/ to /tmp/ paths
            assert retry_until(_f)


@pytest.mark.skipif(
    has_lt_version("3.2a"),
    reason="needs format introduced in tmux >= 3.2a",
)
def test_start_directory_sets_session_path(server: Server) -> None:
    """Test start_directory setting path in session_path."""
    workspace = ConfigReader._from_file(
        test_utils.get_workspace_file(
            "workspace/builder/start_directory_session_path.yaml",
        ),
    )
    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=server)
    builder.build()

    session = builder.session
    expected = f"{session.id}|/usr"

    cmd = server.cmd("list-sessions", "-F", "#{session_id}|#{session_path}")
    assert expected in cmd.stdout


def test_pane_order(session: Session) -> None:
    """Pane ordering based on position in config and ``pane_index``.

    Regression test for https://github.com/tmux-python/tmuxp/issues/15.
    """
    yaml_workspace = test_utils.read_workspace_file(
        "workspace/builder/pane_ordering.yaml",
    ).format(HOME=str(pathlib.Path().home().resolve()))

    # test order of `panes` (and pane_index) above against pane_dirs
    pane_paths = [
        "/usr/bin",
        "/usr",
        "/etc",
        str(pathlib.Path().home().resolve()),
    ]

    workspace = ConfigReader._load(fmt="yaml", content=yaml_workspace)
    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)

    window_count = len(session.windows)  # current window count
    assert len(session.windows) == window_count

    for w, wconf in builder.iter_create_windows(session):
        for _ in builder.iter_create_panes(w, wconf):
            w.select_layout("tiled")  # fix glitch with pane size
            assert len(session.windows) == window_count

        assert isinstance(w, Window)

        assert len(session.windows) == window_count
        window_count += 1

    for w in session.windows:
        pane_base_index = w.show_window_option("pane-base-index", g=True)
        for p_index, p in enumerate(w.panes, start=pane_base_index):
            assert int(p_index) == int(p.index)

            # pane-base-index start at base-index, pane_paths always start
            # at 0 since python list.
            pane_path = pane_paths[p_index - pane_base_index]

            def f(pane_path: str, p: Pane) -> bool:
                p.refresh()
                return p.pane_current_path == pane_path

            _f = functools.partial(f, pane_path=pane_path, p=p)

            assert retry_until(_f)


def test_window_index(
    session: Session,
) -> None:
    """Test window_index respected by workspace builder."""
    proc = session.cmd("show-option", "-gv", "base-index")
    base_index = int(proc.stdout[0])
    name_index_map = {"zero": 0 + base_index, "one": 1 + base_index, "five": 5}

    workspace = ConfigReader._from_file(
        test_utils.get_workspace_file("workspace/builder/window_index.yaml"),
    )
    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)

    for window, _ in builder.iter_create_windows(session):
        expected_index = name_index_map[window.window_name]
        assert int(window.window_index) == expected_index


def test_before_script_throw_error_if_retcode_error(
    server: Server,
) -> None:
    """Test tmuxp configuration before_script when command fails."""
    config_script_fails = test_utils.read_workspace_file(
        "workspace/builder/config_script_fails.yaml",
    )
    yaml_workspace = config_script_fails.format(
        script_failed=FIXTURE_PATH / "script_failed.sh",
    )

    workspace = ConfigReader._load(fmt="yaml", content=yaml_workspace)
    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=server)

    with temp_session(server) as sess:
        session_name = sess.name
        assert session_name is not None

        with pytest.raises(exc.BeforeLoadScriptError):
            builder.build(session=sess)

        result = server.has_session(session_name)
        assert not result, "Kills session if before_script exits with errcode"


def test_before_script_throw_error_if_file_not_exists(
    server: Server,
) -> None:
    """Test tmuxp configuration before_script when script does not exist."""
    config_script_not_exists = test_utils.read_workspace_file(
        "workspace/builder/config_script_not_exists.yaml",
    )
    yaml_workspace = config_script_not_exists.format(
        script_not_exists=FIXTURE_PATH / "script_not_exists.sh",
    )
    workspace = ConfigReader._load(fmt="yaml", content=yaml_workspace)
    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=server)

    with temp_session(server) as session:
        session_name = session.name

        assert session_name is not None
        temp_session_exists = server.has_session(session_name)
        assert temp_session_exists
        with pytest.raises((exc.BeforeLoadScriptNotExists, OSError)) as excinfo:
            builder.build(session=session)
            excinfo.match(r"No such file or directory")
        result = server.has_session(session_name)
        assert not result, "Kills session if before_script doesn't exist"


def test_before_script_true_if_test_passes(
    server: Server,
) -> None:
    """Test tmuxp configuration before_script when command succeeds."""
    config_script_completes = test_utils.read_workspace_file(
        "workspace/builder/config_script_completes.yaml",
    )
    script_complete_sh = FIXTURE_PATH / "script_complete.sh"
    assert script_complete_sh.exists()

    yaml_workspace = config_script_completes.format(script_complete=script_complete_sh)
    workspace = ConfigReader._load(fmt="yaml", content=yaml_workspace)
    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=server)

    with temp_session(server) as session:
        builder.build(session=session)


def test_before_script_true_if_test_passes_with_args(
    server: Server,
) -> None:
    """Test tmuxp configuration before_script when command passes w/ args."""
    config_script_completes = test_utils.read_workspace_file(
        "workspace/builder/config_script_completes.yaml",
    )
    script_complete_sh = FIXTURE_PATH / "script_complete.sh"
    assert script_complete_sh.exists()

    yaml_workspace = config_script_completes.format(script_complete=script_complete_sh)

    workspace = ConfigReader._load(fmt="yaml", content=yaml_workspace)
    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=server)

    with temp_session(server) as session:
        builder.build(session=session)


def test_plugin_system_before_workspace_builder(
    monkeypatch_plugin_test_packages: None,
    session: Session,
) -> None:
    """Test tmuxp configuration plugin hook before workspace builder starts."""
    workspace = ConfigReader._from_file(
        path=test_utils.get_workspace_file("workspace/builder/plugin_bwb.yaml"),
    )
    workspace = loader.expand(workspace)

    builder = WorkspaceBuilder(
        session_config=workspace,
        plugins=load_plugins(workspace),
        server=session.server,
    )
    assert len(builder.plugins) > 0

    builder.build(session=session)

    proc = session.cmd("display-message", "-p", "'#S'")
    assert proc.stdout[0] == "'plugin_test_bwb'"


def test_plugin_system_on_window_create(
    monkeypatch_plugin_test_packages: None,
    session: Session,
) -> None:
    """Test tmuxp configuration plugin hooks work on window creation."""
    workspace = ConfigReader._from_file(
        path=test_utils.get_workspace_file("workspace/builder/plugin_owc.yaml"),
    )
    workspace = loader.expand(workspace)

    builder = WorkspaceBuilder(
        session_config=workspace,
        plugins=load_plugins(workspace),
        server=session.server,
    )
    assert len(builder.plugins) > 0

    builder.build(session=session)

    proc = session.cmd("display-message", "-p", "'#W'")
    assert proc.stdout[0] == "'plugin_test_owc'"


def test_plugin_system_after_window_finished(
    monkeypatch_plugin_test_packages: None,
    session: Session,
) -> None:
    """Test tmuxp configuration plugin hooks work after windows created."""
    workspace = ConfigReader._from_file(
        path=test_utils.get_workspace_file("workspace/builder/plugin_awf.yaml"),
    )
    workspace = loader.expand(workspace)

    builder = WorkspaceBuilder(
        session_config=workspace,
        plugins=load_plugins(workspace),
        server=session.server,
    )
    assert len(builder.plugins) > 0

    builder.build(session=session)

    proc = session.cmd("display-message", "-p", "'#W'")
    assert proc.stdout[0] == "'plugin_test_awf'"


def test_plugin_system_on_window_create_multiple_windows(
    session: Session,
) -> None:
    """Test tmuxp configuration plugin hooks work on windows creation."""
    workspace = ConfigReader._from_file(
        path=test_utils.get_workspace_file(
            "workspace/builder/plugin_owc_multiple_windows.yaml",
        ),
    )
    workspace = loader.expand(workspace)

    builder = WorkspaceBuilder(
        session_config=workspace,
        plugins=load_plugins(workspace),
        server=session.server,
    )
    assert len(builder.plugins) > 0

    builder.build(session=session)

    proc = session.cmd("list-windows", "-F", "'#W'")
    assert "'plugin_test_owc_mw'" in proc.stdout
    assert "'plugin_test_owc_mw_2'" in proc.stdout


def test_plugin_system_after_window_finished_multiple_windows(
    monkeypatch_plugin_test_packages: None,
    session: Session,
) -> None:
    """Test tmuxp configuration plugin hooks work after windows created."""
    workspace = ConfigReader._from_file(
        path=test_utils.get_workspace_file(
            "workspace/builder/plugin_awf_multiple_windows.yaml",
        ),
    )
    workspace = loader.expand(workspace)

    builder = WorkspaceBuilder(
        session_config=workspace,
        plugins=load_plugins(workspace),
        server=session.server,
    )
    assert len(builder.plugins) > 0

    builder.build(session=session)

    proc = session.cmd("list-windows", "-F", "'#W'")
    assert "'plugin_test_awf_mw'" in proc.stdout
    assert "'plugin_test_awf_mw_2'" in proc.stdout


def test_plugin_system_multiple_plugins(
    monkeypatch_plugin_test_packages: None,
    session: Session,
) -> None:
    """Test tmuxp plugin system works with multiple plugins."""
    workspace = ConfigReader._from_file(
        path=test_utils.get_workspace_file(
            "workspace/builder/plugin_multiple_plugins.yaml",
        ),
    )
    workspace = loader.expand(workspace)

    builder = WorkspaceBuilder(
        session_config=workspace,
        plugins=load_plugins(workspace),
        server=session.server,
    )
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


def test_load_configs_same_session(
    server: Server,
) -> None:
    """Test tmuxp configuration can be loaded into same session."""
    workspace = ConfigReader._from_file(
        path=test_utils.get_workspace_file("workspace/builder/three_windows.yaml"),
    )

    builder = WorkspaceBuilder(session_config=workspace, server=server)
    builder.build()

    assert len(server.sessions) == 1
    assert len(server.sessions[0].windows) == 3

    workspace = ConfigReader._from_file(
        path=test_utils.get_workspace_file("workspace/builder/two_windows.yaml"),
    )

    builder = WorkspaceBuilder(session_config=workspace, server=server)
    builder.build()
    assert len(server.sessions) == 2
    assert len(server.sessions[1].windows) == 2

    workspace = ConfigReader._from_file(
        path=test_utils.get_workspace_file("workspace/builder/two_windows.yaml"),
    )

    builder = WorkspaceBuilder(session_config=workspace, server=server)
    builder.build(server.sessions[1], True)

    assert len(server.sessions) == 2
    assert len(server.sessions[1].windows) == 4


def test_load_configs_separate_sessions(
    server: Server,
) -> None:
    """Test workspace builder can load configuration in separate session."""
    workspace = ConfigReader._from_file(
        path=test_utils.get_workspace_file("workspace/builder/three_windows.yaml"),
    )

    builder = WorkspaceBuilder(session_config=workspace, server=server)
    builder.build()

    assert len(server.sessions) == 1
    assert len(server.sessions[0].windows) == 3

    workspace = ConfigReader._from_file(
        path=test_utils.get_workspace_file("workspace/builder/two_windows.yaml"),
    )

    builder = WorkspaceBuilder(session_config=workspace, server=server)
    builder.build()

    assert len(server.sessions) == 2
    assert len(server.sessions[0].windows) == 3
    assert len(server.sessions[1].windows) == 2


def test_find_current_active_pane(
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tests workspace builder can find the current active pane (and session)."""
    workspace = ConfigReader._from_file(
        path=test_utils.get_workspace_file("workspace/builder/three_windows.yaml"),
    )

    builder = WorkspaceBuilder(session_config=workspace, server=server)
    builder.build()

    workspace = ConfigReader._from_file(
        path=test_utils.get_workspace_file("workspace/builder/two_windows.yaml"),
    )

    builder = WorkspaceBuilder(session_config=workspace, server=server)
    builder.build()

    assert len(server.sessions) == 2

    # Assign an active pane to the session
    second_session = server.sessions[1]
    first_pane_on_second_session_id = second_session.windows[0].panes[0].pane_id

    assert first_pane_on_second_session_id is not None
    monkeypatch.setenv("TMUX_PANE", first_pane_on_second_session_id)

    builder = WorkspaceBuilder(session_config=workspace, server=server)

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
    """,
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
    """,
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
  """,
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
  """,
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
    """,
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
    """,
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
  """,
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
  """,
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
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
    yaml: str,
    output: str,
    should_see: bool,
) -> None:
    """Test workspace enters commands to panes in tmuxp configuration."""
    yaml_workspace = tmp_path / "simple.yaml"
    yaml_workspace.write_text(yaml, encoding="utf-8")
    workspace = ConfigReader._from_file(yaml_workspace)
    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)
    builder = WorkspaceBuilder(session_config=workspace, server=server)
    builder.build()

    session = builder.session
    assert isinstance(session, Session)
    pane = session.attached_pane
    assert isinstance(pane, Pane)

    def fn() -> bool:
        captured_pane = "\n".join(pane.capture_pane())

        if should_see:
            return output in captured_pane
        else:
            return output not in captured_pane

    assert retry_until(
        fn,
        1,
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
    """,
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
    """,
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
    """,
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
    """,
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
    """,
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
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
    yaml: str,
    sleep: int,
    output: str,
) -> None:
    """Test sleep commands in tmuxp configuration."""
    yaml_workspace = tmp_path / "simple.yaml"
    yaml_workspace.write_text(yaml, encoding="utf-8")
    workspace = ConfigReader._from_file(yaml_workspace)
    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)
    builder = WorkspaceBuilder(session_config=workspace, server=server)

    start_time = time.process_time()

    builder.build()
    time.sleep(0.5)
    session = builder.session
    assert isinstance(builder.session, Session)
    assert session is not None
    pane = session.attached_pane
    assert isinstance(pane, Pane)

    assert pane is not None

    assert not isinstance(pane.capture_pane, str)
    assert callable(pane.capture_pane)

    while (time.process_time() - start_time) * 1000 < sleep:
        captured_pane = "\n".join(pane.capture_pane())

        assert output not in captured_pane
        time.sleep(0.1)

    captured_pane = "\n".join(pane.capture_pane())
    assert output in captured_pane


def test_first_pane_start_directory(session: Session, tmp_path: pathlib.Path) -> None:
    """Test the first pane start_directory sticks."""
    yaml_workspace = test_utils.get_workspace_file(
        "workspace/builder/first_pane_start_directory.yaml",
    )

    workspace = ConfigReader._from_file(yaml_workspace)
    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    builder.build(session=session)

    assert session == builder.session
    dirs = ["/usr", "/etc"]

    assert session.windows
    window = session.windows[0]
    for path, p in zip(dirs, window.panes):

        def f(path: str, p: Pane) -> bool:
            pane_path = p.pane_current_path
            return (pane_path is not None and path in pane_path) or pane_path == path

        _f = functools.partial(f, path=path, p=p)

        # handle case with OS X adding /private/ to /tmp/ paths
        assert retry_until(_f)


@pytest.mark.skipif(
    has_lt_version("2.9"),
    reason="needs option introduced in tmux >= 2.9",
)
def test_layout_main_horizontal(session: Session) -> None:
    """Test that tmux's main-horizontal layout is used when specified."""
    yaml_workspace = test_utils.get_workspace_file("workspace/builder/three_pane.yaml")
    workspace = ConfigReader._from_file(path=yaml_workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    builder.build(session=session)

    assert session.windows
    window = session.windows[0]

    assert len(window.panes) == 3
    main_horizontal_pane, *panes = window.panes

    def height(p: Pane) -> int:
        return int(p.pane_height) if p.pane_height is not None else 0

    def width(p: Pane) -> int:
        return int(p.pane_width) if p.pane_width is not None else 0

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

    def is_almost_equal(x: int, y: int) -> bool:
        return abs(x - y) <= 1

    assert is_almost_equal(height(panes[0]), height(panes[1]))
    assert is_almost_equal(width(panes[0]), width(panes[1]))


class DefaultSizeNamespaceFixture(t.NamedTuple):
    """Pytest fixture default-size option in tmuxp workspace builder."""

    # pytest parametrize needs a unique id for each fixture
    test_id: str

    # test params
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
    yaml_workspace = test_utils.get_workspace_file(
        "regressions/issue_800_default_size_many_windows.yaml",
    )

    workspace = ConfigReader._from_file(yaml_workspace)
    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)

    if isinstance(confoverrides, dict):
        for k, v in confoverrides.items():
            workspace[k] = v

    if TMUXP_DEFAULT_SIZE is not None:
        monkeypatch.setenv("TMUXP_DEFAULT_SIZE", TMUXP_DEFAULT_SIZE)

    builder = WorkspaceBuilder(session_config=workspace, server=server)

    if raises:
        with pytest.raises(
            (
                LibTmuxException,
                exc.TmuxpException,
                exc.EmptyWorkspaceException,
                ObjectDoesNotExist,
            ),
        ):
            builder.build()

        assert builder is not None
        assert builder.session is not None
        assert isinstance(builder.session, Session)
        assert callable(builder.session.kill)
        builder.session.kill()

        with pytest.raises(libtmux.exc.LibTmuxException, match="no space for new pane"):
            builder.build()
        return

    builder.build()
    assert len(server.sessions) == 1
