"""Test for tmuxp workspace builder."""

from __future__ import annotations

import functools
import logging
import os
import pathlib
import shlex
import textwrap
import time
import typing as t

import libtmux
import pytest
from libtmux._internal.query_list import ObjectDoesNotExist
from libtmux.constants import OptionScope
from libtmux.exc import LibTmuxException
from libtmux.pane import Pane
from libtmux.session import Session
from libtmux.test.retry import retry_until
from libtmux.test.temporary import temp_session
from libtmux.window import Window

from tests.constants import EXAMPLE_PATH, FIXTURE_PATH
from tests.fixtures import utils as test_utils
from tmuxp import exc
from tmuxp._internal.config_reader import ConfigReader
from tmuxp.cli.load import load_plugins
from tmuxp.plugin import TmuxpPlugin
from tmuxp.workspace import builder as builder_module, loader
from tmuxp.workspace.builder import (
    WorkspaceBuilder,
    _wait_for_pane_ready,
    _wait_for_panes_ready,
)

if t.TYPE_CHECKING:
    from libtmux.server import Server

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
        w.set_option("main-pane-height", 50)
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

    assert session.active_window.name == "focused window"

    pane_base_index_ = session.active_window.show_option(
        "pane-base-index",
        global_=True,
    )
    assert isinstance(pane_base_index_, int)
    pane_base_index = int(pane_base_index_)

    pane_base_index = 0 if not pane_base_index else int(pane_base_index)

    # get the pane index for each pane
    pane_base_indexes = [
        int(pane.index)
        for pane in session.active_window.panes
        if pane is not None and pane.index is not None
    ]

    pane_indexes_should_be = [pane_base_index + x for x in range(3)]
    assert pane_indexes_should_be == pane_base_indexes

    w = session.active_window

    assert w.name != "man"

    pane_path = "/usr"
    p = None

    def f_check() -> bool:
        nonlocal p
        p = w.active_pane
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
        p = window3.active_pane
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
        p = w.active_pane
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

        f_ = functools.partial(f, p=p, buffer_name=buffer_name, assertCase=assertCase)

        assert retry_until(f_), f"Unknown sent command: [{sent_cmd}] in {assertCase}"


def test_session_options(session: Session) -> None:
    """Test setting of options to session scope."""
    workspace = ConfigReader._from_file(
        test_utils.get_workspace_file("workspace/builder/session_options.yaml"),
    )
    workspace = loader.expand(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    builder.build(session=session)

    default_shell = session.show_option("default-shell")
    assert isinstance(default_shell, str)
    assert "/bin/sh" in default_shell

    default_command = session.show_option("default-command")
    assert isinstance(default_command, str)
    assert "/bin/sh" in default_command


def test_global_options(session: Session) -> None:
    """Test setting of global options."""
    workspace = ConfigReader._from_file(
        test_utils.get_workspace_file("workspace/builder/global_options.yaml"),
    )
    workspace = loader.expand(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    builder.build(session=session)

    status_position = session.show_option("status-position", global_=True)
    assert isinstance(status_position, str)
    assert "top" in status_position
    assert session.show_option("repeat-time", global_=True) == 493


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

    visual_silence_ = session.show_option("visual-silence", global_=True)
    assert isinstance(visual_silence_, bool)
    assert visual_silence_ is True
    assert repeat_time == session.show_option("repeat-time")
    assert main_pane_height == session.active_window.show_option(
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
        assert w.show_option("main-pane-height") == 5
        assert w.show_option("pane-border-format") == " #P "

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

    for i, pane in enumerate(session.active_window.panes):
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

    for pane in session.active_window.panes:
        assert assert_last_line(
            pane,
            "moo",
        ), "Synchronized command did not execute properly"


class SynchronizePanesFixture(t.NamedTuple):
    """Synchronize-panes command isolation fixture."""

    test_id: str
    yaml: str
    enable_global_sync: bool
    expected_local_sync: bool | None


SYNCHRONIZE_PANES_FIXTURES: list[SynchronizePanesFixture] = [
    SynchronizePanesFixture(
        test_id="window_option",
        yaml=textwrap.dedent(
            """\
session_name: sync-command-test
windows:
- window_name: sync
  options:
    synchronize-panes: on
  panes:
  - shell_command:
    - cmd: echo tmuxp-left-sync-marker
  - shell_command:
    - cmd: echo tmuxp-right-sync-marker
""",
        ),
        enable_global_sync=False,
        expected_local_sync=True,
    ),
    SynchronizePanesFixture(
        test_id="global_default",
        yaml=textwrap.dedent(
            """\
session_name: sync-command-test
windows:
- window_name: sync
  panes:
  - shell_command:
    - cmd: echo tmuxp-left-sync-marker
  - shell_command:
    - cmd: echo tmuxp-right-sync-marker
""",
        ),
        enable_global_sync=True,
        expected_local_sync=None,
    ),
]


class SynchronizePanesExitFixture(t.NamedTuple):
    """Synchronize-panes fixture with a pane that exits during setup."""

    test_id: str
    yaml: str


SYNCHRONIZE_PANES_EXIT_FIXTURES: list[SynchronizePanesExitFixture] = [
    SynchronizePanesExitFixture(
        test_id="pane_exit",
        yaml=textwrap.dedent(
            """\
session_name: sync-exit-test
windows:
- window_name: sync-exit
  options:
    synchronize-panes: on
  panes:
  - shell_command:
    - cmd: printf tmuxp-survivor-marker; sleep 1
  - shell_command:
    - cmd: exit
      sleep_after: 0.3
""",
        ),
    ),
]


@pytest.mark.parametrize(
    list(SynchronizePanesFixture._fields),
    SYNCHRONIZE_PANES_FIXTURES,
    ids=[t.test_id for t in SYNCHRONIZE_PANES_FIXTURES],
)
def test_synchronize_panes_disabled_during_pane_commands(
    tmp_path: pathlib.Path,
    session: Session,
    test_id: str,
    yaml: str,
    enable_global_sync: bool,
    expected_local_sync: bool | None,
) -> None:
    """Per-pane shell commands do not broadcast when synchronize-panes is on."""
    yaml_workspace = tmp_path / f"{test_id}.yaml"
    yaml_workspace.write_text(yaml, encoding="utf-8")
    workspace = ConfigReader._from_file(yaml_workspace)
    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)

    if enable_global_sync:
        session.active_window.set_option(
            "synchronize-panes",
            "on",
            global_=True,
            scope=OptionScope.Window,
        )

    try:
        builder = WorkspaceBuilder(session_config=workspace, server=session.server)
        builder.build(session=session)
        window = session.active_window
        left, right = window.panes

        def capture(pane: Pane) -> str:
            return "\n".join(pane.cmd("capture-pane", "-p", "-J").stdout)

        def commands_stayed_per_pane() -> bool:
            left_text = capture(left)
            right_text = capture(right)
            return (
                "tmuxp-left-sync-marker" in left_text
                and "tmuxp-right-sync-marker" not in left_text
                and "tmuxp-right-sync-marker" in right_text
                and "tmuxp-left-sync-marker" not in right_text
            )

        assert retry_until(commands_stayed_per_pane, 5, interval=0.1), (
            capture(left),
            capture(right),
        )
        assert (
            window.show_option("synchronize-panes", scope=OptionScope.Window)
            is expected_local_sync
        )
        assert (
            window.show_option(
                "synchronize-panes",
                scope=OptionScope.Window,
                include_inherited=True,
            )
            is True
        )
    finally:
        if enable_global_sync:
            session.active_window.set_option(
                "synchronize-panes",
                "off",
                global_=True,
                scope=OptionScope.Window,
            )


@pytest.mark.parametrize(
    list(SynchronizePanesExitFixture._fields),
    SYNCHRONIZE_PANES_EXIT_FIXTURES,
    ids=[t.test_id for t in SYNCHRONIZE_PANES_EXIT_FIXTURES],
)
def test_synchronize_panes_ignores_exited_targets(
    tmp_path: pathlib.Path,
    session: Session,
    test_id: str,
    yaml: str,
) -> None:
    """Exiting startup panes do not break temporary sync restoration."""
    yaml_workspace = tmp_path / f"{test_id}.yaml"
    yaml_workspace.write_text(yaml, encoding="utf-8")
    workspace = ConfigReader._from_file(yaml_workspace)
    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    builder.build(session=session)
    window = session.active_window

    def pane_count() -> bool:
        return len(window.panes) == 1

    assert retry_until(pane_count, 5, interval=0.1)


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

        f_ = functools.partial(f, w=w)

        retry_until(f_)

        assert w.name != "top"


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


def test_automatic_rename_option(
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test workspace builder with automatic renaming enabled."""
    monkeypatch.setenv("DISABLE_AUTO_TITLE", "true")
    monkeypatch.setenv("ROWS", "36")

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
        assert w.show_option("automatic-rename") is True
        return w.name in {
            pathlib.Path(os.getenv("SHELL", "bash")).name,
            portable_command,
        }

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

    for path, window in zip(dirs, session.windows, strict=False):
        for p in window.panes:

            def f(path: str, p: Pane) -> bool:
                pane_path = p.pane_current_path
                return (
                    pane_path is not None and path in pane_path
                ) or pane_path == path

            f_ = functools.partial(f, path=path, p=p)

            # handle case with OS X adding /private/ to /tmp/ paths
            assert retry_until(f_)


def test_build_dispatches_window_commands_before_later_start_directory(
    session: Session,
    tmp_path: pathlib.Path,
) -> None:
    """Earlier window commands can prepare a later window's start_directory."""
    late_dir = tmp_path / "late-dir"
    yaml_config = textwrap.dedent(
        f"""\
session_name: window-command-order
windows:
- window_name: bootstrap
  panes:
  - shell_command:
    - cmd: mkdir -p {shlex.quote(str(late_dir))}
      sleep_after: 0.2
- window_name: dependent
  start_directory: {late_dir!s}
  panes:
  - shell_command: []
""",
    )
    workspace = ConfigReader._load(fmt="yaml", content=yaml_config)
    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    builder.build(session=session)

    dependent = session.windows.get(window_name="dependent")
    assert dependent is not None
    pane = dependent.active_pane
    assert pane is not None

    def has_late_dir() -> bool:
        return pane.pane_current_path == str(late_dir)

    assert retry_until(has_late_dir)


class SameWindowStartDirectoryFixture(t.NamedTuple):
    """Same-window start_directory dependency fixture."""

    test_id: str
    later_pane_yaml: str


SAME_WINDOW_START_DIRECTORY_FIXTURES: list[SameWindowStartDirectoryFixture] = [
    SameWindowStartDirectoryFixture(
        test_id="pane_start_directory",
        later_pane_yaml="  - shell_command: []\n    start_directory: {late_dir!s}\n",
    ),
]


@pytest.mark.parametrize(
    list(SameWindowStartDirectoryFixture._fields),
    SAME_WINDOW_START_DIRECTORY_FIXTURES,
    ids=[t.test_id for t in SAME_WINDOW_START_DIRECTORY_FIXTURES],
)
def test_build_dispatches_same_window_commands_before_later_start_directory(
    session: Session,
    tmp_path: pathlib.Path,
    test_id: str,
    later_pane_yaml: str,
) -> None:
    """Earlier pane commands can prepare a later pane's start_directory."""
    late_dir = tmp_path / test_id / "late-dir"
    yaml_config = textwrap.dedent(
        f"""\
session_name: same-window-command-order
windows:
- window_name: dependent
  panes:
  - shell_command:
    - cmd: mkdir -p {shlex.quote(str(late_dir))}
      sleep_after: 0.2
{later_pane_yaml.format(late_dir=late_dir)}
""",
    )
    workspace = ConfigReader._load(fmt="yaml", content=yaml_config)
    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    builder.build(session=session)

    dependent = session.windows.get(window_name="dependent")
    assert dependent is not None
    panes = dependent.panes
    assert len(panes) == 2
    pane = panes[1]

    def has_late_dir() -> bool:
        return pane.pane_current_path == str(late_dir)

    assert retry_until(has_late_dir)


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

    for path, window in zip(dirs, session.windows, strict=False):
        for p in window.panes:

            def f(path: str, p: Pane) -> bool:
                pane_path = p.pane_current_path
                return (
                    pane_path is not None and path in pane_path
                ) or pane_path == path

            f_ = functools.partial(f, path=path, p=p)

            # handle case with OS X adding /private/ to /tmp/ paths
            assert retry_until(f_)


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
        pane_base_index = w.show_option("pane-base-index", global_=True)
        assert pane_base_index is not None
        pane_base_index = int(pane_base_index)
        for p_index, p in enumerate(w.panes, start=pane_base_index):
            assert p.index is not None
            assert int(p_index) == int(p.index)

            # pane-base-index start at base-index, pane_paths always start
            # at 0 since python list.
            pane_path = pane_paths[p_index - pane_base_index]

            def f(pane_path: str, p: Pane) -> bool:
                p.refresh()
                return p.pane_current_path == pane_path

            f_ = functools.partial(f, pane_path=pane_path, p=p)

            assert retry_until(f_)


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
    caplog: pytest.LogCaptureFixture,
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

        with (
            caplog.at_level(logging.ERROR, logger="tmuxp.workspace.builder"),
            pytest.raises(exc.BeforeLoadScriptError),
        ):
            builder.build(session=sess)

        result = server.has_session(session_name)
        assert not result, "Kills session if before_script exits with errcode"

    error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert len(error_records) >= 1
    assert error_records[0].msg == "before script failed"
    assert hasattr(error_records[0], "tmux_session")


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


class WorkspaceEnterFixture(t.NamedTuple):
    """Test fixture for workspace enter behavior verification."""

    test_id: str
    yaml: str
    output: str
    should_see: bool


WORKSPACE_ENTER_FIXTURES: list[WorkspaceEnterFixture] = [
    WorkspaceEnterFixture(
        test_id="pane_enter_false_shortform",
        yaml=textwrap.dedent(
            """
session_name: Should not execute
windows:
- panes:
  - shell_command: echo "___$((1 + 3))___"
    enter: false
    """,
        ),
        output="___4___",
        should_see=False,
    ),
    WorkspaceEnterFixture(
        test_id="pane_enter_false_longform",
        yaml=textwrap.dedent(
            """
session_name: Should not execute
windows:
- panes:
  - shell_command:
    - echo "___$((1 + 3))___"
    enter: false
    """,
        ),
        output="___4___",
        should_see=False,
    ),
    WorkspaceEnterFixture(
        test_id="pane_enter_default_shortform",
        yaml=textwrap.dedent(
            """
session_name: Should execute
windows:
- panes:
  - shell_command: echo "___$((1 + 3))___"
  """,
        ),
        output="___4___",
        should_see=True,
    ),
    WorkspaceEnterFixture(
        test_id="pane_enter_default_longform",
        yaml=textwrap.dedent(
            """
session_name: Should execute
windows:
- panes:
  - shell_command:
    - echo "___$((1 + 3))___"
  """,
        ),
        output="___4___",
        should_see=True,
    ),
    WorkspaceEnterFixture(
        test_id="pane_command_enter_false_shortform",
        yaml=textwrap.dedent(
            """
session_name: Should not execute
windows:
- panes:
  - shell_command:
    - cmd: echo "___$((1 + 3))___"
      enter: false
    """,
        ),
        output="___4___",
        should_see=False,
    ),
    WorkspaceEnterFixture(  # NOQA: PT014 RUF100
        test_id="pane_command_enter_false_longform",
        yaml=textwrap.dedent(
            """
session_name: Should not execute
windows:
- panes:
  - shell_command:
    - cmd: echo "___$((1 + 3))___"
      enter: false
    """,
        ),
        output="___4___",
        should_see=False,
    ),
    WorkspaceEnterFixture(  # NOQA: PT014 RUF100
        test_id="pane_command_enter_default_shortform",
        yaml=textwrap.dedent(
            """
session_name: Should execute
windows:
- panes:
  - shell_command: echo "___$((1 + 3))___"
  """,
        ),
        output="___4___",
        should_see=True,
    ),
    WorkspaceEnterFixture(
        test_id="pane_command_enter_default_longform",
        yaml=textwrap.dedent(
            """
session_name: Should execute
windows:
- panes:
  - shell_command:
    - cmd: echo "other command"
    - cmd: echo "___$((1 + 3))___"
  """,
        ),
        output="___4___",
        should_see=True,
    ),
]


@pytest.mark.parametrize(
    list(WorkspaceEnterFixture._fields),
    WORKSPACE_ENTER_FIXTURES,
    ids=[test.test_id for test in WORKSPACE_ENTER_FIXTURES],
)
def test_load_workspace_enter(
    tmp_path: pathlib.Path,
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
    test_id: str,
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
    pane = session.active_pane
    assert isinstance(pane, Pane)

    def fn() -> bool:
        captured_pane = "\n".join(pane.capture_pane())

        if should_see:
            return output in captured_pane
        return output not in captured_pane

    assert retry_until(
        fn,
        1,
    ), f"Should{' ' if should_see else 'not '} output in captured pane"


class WorkspaceSleepFixture(t.NamedTuple):
    """Test fixture for workspace sleep behavior verification."""

    test_id: str
    yaml: str
    sleep: float
    output: str


WORKSPACE_SLEEP_FIXTURES: list[WorkspaceSleepFixture] = [
    WorkspaceSleepFixture(
        test_id="command_level_sleep_shortform",
        yaml=textwrap.dedent(
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
        sleep=0.5,
        output="___4___",
    ),
    WorkspaceSleepFixture(
        test_id="command_level_pane_sleep_longform",
        yaml=textwrap.dedent(
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
        sleep=1.25,
        output="___4___",
    ),
    WorkspaceSleepFixture(
        test_id="pane_sleep_shortform",
        yaml=textwrap.dedent(
            """
session_name: Should not execute
windows:
- panes:
  - shell_command:
    - cmd: echo "___$((1 + 3))___"
    sleep_before: .5
    """,
        ),
        sleep=0.5,
        output="___4___",
    ),
    WorkspaceSleepFixture(
        test_id="pane_sleep_longform",
        yaml=textwrap.dedent(
            """
session_name: Should not execute
windows:
- panes:
  - shell_command:
    - cmd: echo "___$((1 + 3))___"
    sleep_before: 1
    """,
        ),
        sleep=1,
        output="___4___",
    ),
    WorkspaceSleepFixture(
        test_id="shell_before_before_command_level",
        yaml=textwrap.dedent(
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
        sleep=0.5,
        output="___4___",
    ),
]


@pytest.mark.parametrize(
    list(WorkspaceSleepFixture._fields),
    WORKSPACE_SLEEP_FIXTURES,
    ids=[test.test_id for test in WORKSPACE_SLEEP_FIXTURES],
)
@pytest.mark.flaky(reruns=3)
def test_load_workspace_sleep(
    tmp_path: pathlib.Path,
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
    test_id: str,
    yaml: str,
    sleep: float,
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
    pane = session.active_pane
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
    for path, p in zip(dirs, window.panes, strict=False):

        def f(path: str, p: Pane) -> bool:
            pane_path = p.pane_current_path
            return (pane_path is not None and path in pane_path) or pane_path == path

        f_ = functools.partial(f, path=path, p=p)

        # handle case with OS X adding /private/ to /tmp/ paths
        assert retry_until(f_)


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
    assert all(pane_heights[0] == pane_height for pane_height in pane_heights), (
        "The bottom row should be uniform height"
    )
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
    TMUXP_DEFAULT_SIZE: str | None
    raises: bool
    confoverrides: dict[str, t.Any]


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
def test_issue_800_default_size_many_windows(
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
    test_id: str,
    TMUXP_DEFAULT_SIZE: str | None,
    raises: bool,
    confoverrides: dict[str, t.Any],
) -> None:
    """Recreate default-size issue.

    v1.13.1 added a default-size, but this can break building workspaces with
    a lot of panes.

    See also: https://github.com/tmux-python/tmuxp/issues/800

    2024-04-07: This test isn't being used as of this date, as default-size is totally
    unused in builder.py.
    """
    monkeypatch.setenv("ROWS", "36")

    yaml_workspace = test_utils.get_workspace_file(
        "regressions/issue_800_default_size_many_windows.yaml",
    )

    workspace = ConfigReader._from_file(yaml_workspace)
    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)

    if isinstance(confoverrides, dict):
        for k, v in confoverrides.items():
            workspace[k] = v

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

        # tmux 3.7 reworded this error from "no space for new pane" to
        # "size or position no space for a new pane"; the optional "a "
        # matches both wordings.
        with pytest.raises(
            libtmux.exc.LibTmuxException,
            match=r"no space for (a )?new pane",
        ):
            builder.build()
        return

    builder.build()
    assert len(server.sessions) == 1


def test_wait_for_pane_ready_returns_true(session: Session) -> None:
    """Verify _wait_for_pane_ready detects shell prompt."""
    pane = session.active_window.active_pane
    assert pane is not None
    result = _wait_for_pane_ready(pane, timeout=2.0)
    assert result is True


def test_wait_for_pane_ready_timeout(session: Session) -> None:
    """Verify _wait_for_pane_ready returns False on timeout for non-shell."""
    window = session.active_window
    assert window.active_pane is not None
    new_pane = window.active_pane.split(shell="sleep 999")
    assert new_pane is not None
    result = _wait_for_pane_ready(new_pane, timeout=0.2)
    assert result is False


def test_wait_for_panes_ready_all_ready(session: Session) -> None:
    """The shared barrier reports every default-shell pane ready."""
    window = session.active_window
    first = window.active_pane
    assert first is not None
    second = first.split()
    assert second is not None

    result = _wait_for_panes_ready([first, second], timeout=5.0)

    assert result == {first.pane_id: True, second.pane_id: True}


def test_wait_for_panes_ready_mixed(session: Session) -> None:
    """The shared barrier times out only the pane that never draws a prompt."""
    window = session.active_window
    first = window.active_pane
    assert first is not None
    sleeper = first.split(shell="sleep 999")
    assert sleeper is not None
    assert first.pane_id is not None
    assert sleeper.pane_id is not None

    result = _wait_for_panes_ready([first, sleeper], timeout=0.5)

    assert result[first.pane_id] is True
    assert result[sleeper.pane_id] is False


class PaneReadinessFixture(t.NamedTuple):
    """Test fixture for pane readiness call count verification."""

    test_id: str
    yaml: str
    expected_wait_count: int


PANE_READINESS_FIXTURES: list[PaneReadinessFixture] = [
    PaneReadinessFixture(
        test_id="waits_for_pane_with_commands",
        yaml=textwrap.dedent(
            """\
session_name: readiness-test
windows:
- panes:
  - shell_command:
    - cmd: echo hello
  - shell_command:
    - cmd: echo world
""",
        ),
        expected_wait_count=2,
    ),
    PaneReadinessFixture(
        test_id="waits_for_pane_without_commands",
        yaml=textwrap.dedent(
            """\
session_name: readiness-test
windows:
- panes:
  - shell_command:
    - cmd: echo hello
  - shell_command: []
""",
        ),
        expected_wait_count=2,
    ),
    PaneReadinessFixture(
        test_id="skips_pane_with_custom_shell",
        yaml=textwrap.dedent(
            """\
session_name: readiness-test
windows:
- panes:
  - shell_command:
    - cmd: echo hello
  - shell: sleep 999
    shell_command:
    - cmd: echo world
""",
        ),
        expected_wait_count=1,
    ),
    PaneReadinessFixture(
        test_id="skips_all_panes_with_window_shell",
        yaml=textwrap.dedent(
            """\
session_name: readiness-test
windows:
- window_shell: top
  panes:
  - shell_command: []
  - shell_command: []
""",
        ),
        expected_wait_count=0,
    ),
]


@pytest.mark.parametrize(
    list(PaneReadinessFixture._fields),
    PANE_READINESS_FIXTURES,
    ids=[t.test_id for t in PANE_READINESS_FIXTURES],
)
def test_pane_readiness_waits_for_default_shell_panes(
    tmp_path: pathlib.Path,
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
    test_id: str,
    yaml: str,
    expected_wait_count: int,
) -> None:
    """Only default-shell panes are submitted to the readiness barrier."""
    waited: list[str] = []
    original = builder_module._wait_for_panes_ready

    def recording_barrier(
        panes: list[Pane],
        timeout: float = 2.0,
        interval: float = 0.05,
    ) -> dict[str, bool]:
        waited.extend(p.pane_id for p in panes if p.pane_id is not None)
        return original(panes, timeout=timeout, interval=interval)

    monkeypatch.setattr(builder_module, "_wait_for_panes_ready", recording_barrier)

    yaml_workspace = tmp_path / "readiness.yaml"
    yaml_workspace.write_text(yaml, encoding="utf-8")
    workspace = ConfigReader._from_file(yaml_workspace)
    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=server)
    builder.build()
    assert len(waited) == expected_wait_count


def test_select_layout_called_once_per_window(
    tmp_path: pathlib.Path,
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """select_layout runs once per window, after the readiness barrier."""
    call_count = 0
    original_select_layout = Window.select_layout

    def counting_layout(self: Window, layout: str | None = None) -> Window:
        nonlocal call_count
        call_count += 1
        return original_select_layout(self, layout)

    monkeypatch.setattr(Window, "select_layout", counting_layout)

    yaml_config = textwrap.dedent(
        """\
session_name: layout-test
windows:
- layout: main-vertical
  panes:
  - shell_command: []
  - shell_command: []
  - shell_command: []
""",
    )

    yaml_workspace = tmp_path / "layout.yaml"
    yaml_workspace.write_text(yaml_config, encoding="utf-8")
    workspace = ConfigReader._from_file(yaml_workspace)
    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=server)
    builder.build()
    # One window, one layout pass — no per-pane and no duplicate build() pass.
    assert call_count == 1


def test_split_target_refreshes_without_readiness_wait(
    tmp_path: pathlib.Path,
    session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Normal pane splitting refreshes target state without prompt waiting."""
    events: list[str] = []
    original_refresh = Pane.refresh
    original_split = Pane.split

    def recording_refresh(self: Pane) -> None:
        events.append("refresh")
        return original_refresh(self)

    def recording_split(self: Pane, *args: t.Any, **kwargs: t.Any) -> Pane:
        events.append("split")
        return original_split(self, *args, **kwargs)

    def recording_barrier(
        panes: list[Pane],
        timeout: float = 2.0,
        interval: float = 0.05,
    ) -> dict[str, bool]:
        events.append("wait")
        return {pane.pane_id: True for pane in panes if pane.pane_id is not None}

    monkeypatch.setattr(Pane, "refresh", recording_refresh)
    monkeypatch.setattr(Pane, "split", recording_split)
    monkeypatch.setattr(builder_module, "_wait_for_panes_ready", recording_barrier)

    yaml_config = textwrap.dedent(
        """\
session_name: split-refresh-test
windows:
- panes:
  - shell_command: []
  - shell_command: []
""",
    )
    yaml_workspace = tmp_path / "split_refresh.yaml"
    yaml_workspace.write_text(yaml_config, encoding="utf-8")
    workspace = ConfigReader._from_file(yaml_workspace)
    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    builder._create_window_panes(session.active_window, workspace["windows"][0])

    assert "wait" not in events
    assert events[:2] == ["refresh", "split"]


def test_build_waits_for_each_window_before_dispatch(
    tmp_path: pathlib.Path,
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """build() waits per window so earlier commands run before later windows."""
    barrier_sizes: list[int] = []
    original = builder_module._wait_for_panes_ready

    def recording_barrier(
        panes: list[Pane],
        timeout: float = 2.0,
        interval: float = 0.05,
    ) -> dict[str, bool]:
        barrier_sizes.append(len(panes))
        return original(panes, timeout=timeout, interval=interval)

    monkeypatch.setattr(builder_module, "_wait_for_panes_ready", recording_barrier)

    yaml_config = textwrap.dedent(
        """\
session_name: barrier-test
windows:
- window_name: one
  layout: tiled
  panes:
  - shell_command: []
  - shell_command: []
- window_name: two
  layout: tiled
  panes:
  - shell_command: []
  - shell_command: []
""",
    )
    yaml_workspace = tmp_path / "barrier.yaml"
    yaml_workspace.write_text(yaml_config, encoding="utf-8")
    workspace = ConfigReader._from_file(yaml_workspace)
    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=server)
    builder.build()

    assert barrier_sizes == [2, 2]


def test_layout_runs_after_readiness_barrier(
    tmp_path: pathlib.Path,
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Each window is laid out after that window's readiness barrier.

    This is the issue #365 safety invariant: a pane must draw its prompt before
    it is resized, so every ``select_layout`` must follow a barrier.
    """
    events: list[str] = []
    original_barrier = builder_module._wait_for_panes_ready
    original_select_layout = Window.select_layout

    def traced_barrier(
        panes: list[Pane],
        timeout: float = 2.0,
        interval: float = 0.05,
    ) -> dict[str, bool]:
        result = original_barrier(panes, timeout=timeout, interval=interval)
        events.append("barrier")
        return result

    def traced_layout(self: Window, layout: str | None = None) -> Window:
        events.append("layout")
        return original_select_layout(self, layout)

    monkeypatch.setattr(builder_module, "_wait_for_panes_ready", traced_barrier)
    monkeypatch.setattr(Window, "select_layout", traced_layout)

    yaml_config = textwrap.dedent(
        """\
session_name: ordering-test
windows:
- window_name: one
  layout: tiled
  panes:
  - shell_command: []
  - shell_command: []
- window_name: two
  layout: tiled
  panes:
  - shell_command: []
""",
    )
    yaml_workspace = tmp_path / "ordering.yaml"
    yaml_workspace.write_text(yaml_config, encoding="utf-8")
    workspace = ConfigReader._from_file(yaml_workspace)
    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=server)
    builder.build()

    assert "barrier" in events
    assert "layout" in events
    assert events == ["barrier", "layout", "barrier", "layout"]


class _HookOrderRecorder(TmuxpPlugin):
    """Plugin that records the order its lifecycle hooks fire."""

    def __init__(self, calls: list[str]) -> None:
        self.calls = calls

    def before_workspace_builder(self, session: Session) -> None:
        """Record the session-level pre-build hook."""
        self.calls.append("before_workspace_builder")

    def on_window_create(self, window: Window) -> None:
        """Record the per-window creation hook."""
        self.calls.append(f"on_window_create:{window.name}")

    def after_window_finished(self, window: Window) -> None:
        """Record the per-window completion hook."""
        self.calls.append(f"after_window_finished:{window.name}")


class PluginHookOrderFixture(t.NamedTuple):
    """Expected plugin hook firing order for a workspace config."""

    test_id: str
    yaml: str
    expected_order: list[str]


PLUGIN_HOOK_ORDER_FIXTURES: list[PluginHookOrderFixture] = [
    PluginHookOrderFixture(
        test_id="single_window",
        yaml=textwrap.dedent(
            """\
session_name: hook-order
windows:
- window_name: one
  panes:
  - shell_command: []
""",
        ),
        expected_order=[
            "before_workspace_builder",
            "on_window_create:one",
            "after_window_finished:one",
        ],
    ),
    PluginHookOrderFixture(
        test_id="interleaves_create_and_finish",
        yaml=textwrap.dedent(
            """\
session_name: hook-order
windows:
- window_name: one
  panes:
  - shell_command: []
- window_name: two
  panes:
  - shell_command: []
""",
        ),
        expected_order=[
            "before_workspace_builder",
            "on_window_create:one",
            "after_window_finished:one",
            "on_window_create:two",
            "after_window_finished:two",
        ],
    ),
]


@pytest.mark.parametrize(
    list(PluginHookOrderFixture._fields),
    PLUGIN_HOOK_ORDER_FIXTURES,
    ids=[f.test_id for f in PLUGIN_HOOK_ORDER_FIXTURES],
)
def test_plugin_hook_order(
    tmp_path: pathlib.Path,
    server: Server,
    test_id: str,
    yaml: str,
    expected_order: list[str],
) -> None:
    """Per-window create and finish hooks follow config order."""
    calls: list[str] = []

    yaml_workspace = tmp_path / "hook_order.yaml"
    yaml_workspace.write_text(yaml, encoding="utf-8")
    workspace = ConfigReader._from_file(yaml_workspace)
    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)

    builder = WorkspaceBuilder(
        session_config=workspace,
        plugins=[_HookOrderRecorder(calls)],
        server=server,
    )
    builder.build()

    assert calls == expected_order


def test_builder_logs_session_created(
    server: Server,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """WorkspaceBuilder.build() logs INFO with tmux_session extra."""
    workspace = {
        "session_name": "test_log_session",
        "windows": [
            {
                "window_name": "main",
                "panes": [
                    {"shell_command": []},
                ],
            },
        ],
    }
    builder = WorkspaceBuilder(session_config=workspace, server=server)

    with caplog.at_level(logging.DEBUG, logger="tmuxp.workspace.builder"):
        builder.build()

    session_logs = [
        r
        for r in caplog.records
        if hasattr(r, "tmux_session") and r.msg == "session created"
    ]
    assert len(session_logs) >= 1
    assert session_logs[0].tmux_session == "test_log_session"

    # Verify workspace built log
    built_logs = [r for r in caplog.records if r.msg == "workspace built"]
    assert len(built_logs) >= 1

    builder.session.kill()


def test_builder_logs_window_and_pane_creation(
    server: Server,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """WorkspaceBuilder logs DEBUG with tmux_window and tmux_pane extra."""
    workspace = {
        "session_name": "test_log_wp",
        "windows": [
            {
                "window_name": "editor",
                "panes": [
                    {"shell_command": [{"cmd": "echo hello"}]},
                    {"shell_command": []},
                ],
            },
        ],
    }
    builder = WorkspaceBuilder(session_config=workspace, server=server)

    with caplog.at_level(logging.DEBUG, logger="tmuxp.workspace.builder"):
        builder.build()

    window_logs = [
        r
        for r in caplog.records
        if hasattr(r, "tmux_window") and r.msg == "window created"
    ]
    assert len(window_logs) >= 1
    assert window_logs[0].tmux_window == "editor"

    pane_logs = [
        r for r in caplog.records if hasattr(r, "tmux_pane") and r.msg == "pane created"
    ]
    assert len(pane_logs) >= 1

    cmd_logs = [r for r in caplog.records if r.msg == "sent command %s"]
    assert len(cmd_logs) >= 1

    builder.session.kill()
