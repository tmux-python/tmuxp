"""Test for tmuxp workspace builder."""

from __future__ import annotations

import functools
import logging
import os
import pathlib
import textwrap
import time
import typing as t

import libtmux
import pytest
from libtmux._internal.query_list import ObjectDoesNotExist
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
from tmuxp.workspace import builder as builder_module, loader
from tmuxp.workspace.builder import WorkspaceBuilder, _wait_for_pane_ready

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


def test_synchronize(
    session: Session,
) -> None:
    """Test synchronize config key desugars to synchronize-panes option."""
    workspace = ConfigReader._from_file(
        test_utils.get_workspace_file("workspace/builder/synchronize.yaml"),
    )
    workspace = loader.expand(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    builder.build(session=session)

    windows = session.windows
    assert len(windows) == 3

    synced_before = windows[0]
    synced_after = windows[1]
    not_synced = windows[2]

    assert synced_before.show_option("synchronize-panes") is True
    assert synced_after.show_option("synchronize-panes") is True
    assert not_synced.show_option("synchronize-panes") is not True


def test_shell_command_after(
    session: Session,
) -> None:
    """Test shell_command_after sends commands to all panes after window creation."""
    workspace = ConfigReader._from_file(
        test_utils.get_workspace_file("workspace/builder/shell_command_after.yaml"),
    )
    workspace = loader.expand(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    builder.build(session=session)

    windows = session.windows
    assert len(windows) == 2

    after_window = windows[0]
    no_after_window = windows[1]

    for pane in after_window.panes:

        def check(p: Pane = pane) -> bool:
            return "__AFTER__" in "\n".join(p.capture_pane())

        assert retry_until(check), f"Expected __AFTER__ in pane {pane.pane_id}"

    for pane in no_after_window.panes:
        captured = "\n".join(pane.capture_pane())
        assert "__AFTER__" not in captured


def test_pane_titles(
    session: Session,
) -> None:
    """Test pane title config keys set pane-border-status and pane titles."""
    workspace = ConfigReader._from_file(
        test_utils.get_workspace_file("workspace/builder/pane_titles.yaml"),
    )
    workspace = loader.expand(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    builder.build(session=session)

    window = session.windows[0]
    assert window.show_option("pane-border-status") == "top"
    assert window.show_option("pane-border-format") == "#{pane_index}: #{pane_title}"

    panes = window.panes
    assert len(panes) == 3

    def check_title(p: Pane, expected: str) -> bool:
        p.refresh()
        return p.pane_title == expected

    assert retry_until(
        functools.partial(check_title, panes[0], "editor"),
    ), f"Expected title 'editor', got '{panes[0].pane_title}'"
    assert retry_until(
        functools.partial(check_title, panes[1], "runner"),
    ), f"Expected title 'runner', got '{panes[1].pane_title}'"


def test_here_mode(
    session: Session,
) -> None:
    """Test --here mode reuses current window and renames session."""
    workspace = ConfigReader._from_file(
        test_utils.get_workspace_file("workspace/builder/here_mode.yaml"),
    )
    workspace = loader.expand(workspace)

    # Capture original window ID to verify reuse
    original_window = session.active_window
    original_window_id = original_window.window_id
    original_session_name = session.name

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    builder.build(session=session, here=True)

    # Session should be renamed
    session.refresh()
    assert session.name == "here-session"
    assert session.name != original_session_name

    windows = session.windows
    assert len(windows) == 2

    # First window should be the reused original window (same ID)
    reused_window = windows[0]
    assert reused_window.window_id == original_window_id
    assert reused_window.name == "reused"

    # Second window should be newly created
    new_window = windows[1]
    assert new_window.name == "new-win"
    assert new_window.window_id != original_window_id


def test_here_mode_start_directory_special_chars(
    session: Session,
    tmp_path: pathlib.Path,
) -> None:
    """Test --here mode with special characters in start_directory."""
    test_dir = tmp_path / "dir with 'quotes' & spaces"
    test_dir.mkdir()

    workspace = ConfigReader._from_file(
        test_utils.get_workspace_file("workspace/builder/here_mode.yaml"),
    )
    workspace = loader.expand(workspace)
    workspace["start_directory"] = str(test_dir)
    workspace = loader.trickle(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    builder.build(session=session, here=True)

    reused_window = session.windows[0]
    pane = reused_window.active_pane
    assert pane is not None

    expected_path = os.path.realpath(str(test_dir))

    def check_path() -> bool:
        return pane.pane_current_path == expected_path

    assert retry_until(check_path), (
        f"Expected {expected_path}, got {pane.pane_current_path}"
    )


def test_here_mode_cleans_existing_panes(
    session: Session,
) -> None:
    """Test --here mode removes extra panes before rebuilding."""
    # Start with a 2-pane window
    original_window = session.active_window
    original_window.split()
    assert len(original_window.panes) == 2

    workspace = ConfigReader._from_file(
        test_utils.get_workspace_file("workspace/builder/here_mode.yaml"),
    )
    workspace = loader.expand(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    builder.build(session=session, here=True)

    session.refresh()
    reused_window = session.windows[0]
    # Config has 1 pane in first window — should be exactly 1, not 3
    assert len(reused_window.panes) == 1


class HereDuplicateFixture(t.NamedTuple):
    """Fixture for --here duplicate session name detection."""

    test_id: str
    config_session_name: str
    expect_error: bool


HERE_DUPLICATE_FIXTURES: list[HereDuplicateFixture] = [
    HereDuplicateFixture(
        test_id="same-name-no-rename",
        config_session_name="__CURRENT__",
        expect_error=False,
    ),
    HereDuplicateFixture(
        test_id="different-name-no-conflict",
        config_session_name="unique_target",
        expect_error=False,
    ),
    HereDuplicateFixture(
        test_id="name-conflict-with-existing",
        config_session_name="__EXISTING__",
        expect_error=True,
    ),
]


@pytest.mark.parametrize(
    list(HereDuplicateFixture._fields),
    HERE_DUPLICATE_FIXTURES,
    ids=[f.test_id for f in HERE_DUPLICATE_FIXTURES],
)
def test_here_mode_duplicate_session_name(
    session: Session,
    test_id: str,
    config_session_name: str,
    expect_error: bool,
) -> None:
    """--here mode detects duplicate session names before renaming."""
    server = session.server

    # Create a second session to conflict with
    existing = server.new_session(session_name="existing_blocker")

    # Resolve sentinel values
    if config_session_name == "__CURRENT__":
        target_name = session.name
    elif config_session_name == "__EXISTING__":
        target_name = existing.name
    else:
        target_name = config_session_name

    workspace = ConfigReader._from_file(
        test_utils.get_workspace_file("workspace/builder/here_mode.yaml"),
    )
    workspace = loader.expand(workspace)
    workspace["session_name"] = target_name

    builder = WorkspaceBuilder(session_config=workspace, server=server)

    if expect_error:
        with pytest.raises(exc.TmuxpException, match="session already exists"):
            builder.build(session=session, here=True)
    else:
        builder.build(session=session, here=True)


def test_here_mode_provisions_environment(
    session: Session,
) -> None:
    """--here mode sets environment via session and respawn-pane, not send_keys."""
    from libtmux.test.retry import retry_until

    workspace: dict[str, t.Any] = {
        "session_name": session.name,
        "windows": [
            {
                "window_name": "env-test",
                "environment": {"TMUXP_HERE_TEST": "hello_here"},
                "panes": [
                    {"shell_command": ["echo $TMUXP_HERE_TEST"]},
                ],
            },
        ],
    }
    workspace = loader.expand(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    builder.build(session=session, here=True)

    # Verify env var is set at session level (tmux primitive)
    env = session.show_environment()
    assert env.get("TMUXP_HERE_TEST") == "hello_here"

    # Verify the respawned pane also sees the var
    pane = session.active_window.active_pane
    assert pane is not None

    assert retry_until(
        lambda: "hello_here" in "\n".join(pane.capture_pane()),
        seconds=5,
    )


# --- respawn-pane provisioning tests (f5f490a8, 0504d1b4) ---


class HereRespawnFixture(t.NamedTuple):
    """Fixture for --here respawn-pane provisioning scenarios."""

    test_id: str
    start_directory: bool
    environment: dict[str, str] | None
    window_shell: str | None
    expect_respawn: bool


HERE_RESPAWN_FIXTURES: list[HereRespawnFixture] = [
    HereRespawnFixture(
        test_id="dir-only",
        start_directory=True,
        environment=None,
        window_shell=None,
        expect_respawn=True,
    ),
    HereRespawnFixture(
        test_id="env-only",
        start_directory=False,
        environment={"TMUXP_TEST_VAR": "respawn_val"},
        window_shell=None,
        expect_respawn=True,
    ),
    HereRespawnFixture(
        test_id="dir-and-env",
        start_directory=True,
        environment={"TMUXP_DIR_ENV": "combined"},
        window_shell=None,
        expect_respawn=True,
    ),
    HereRespawnFixture(
        test_id="nothing-to-provision",
        start_directory=False,
        environment=None,
        window_shell=None,
        expect_respawn=False,
    ),
]


@pytest.mark.parametrize(
    list(HereRespawnFixture._fields),
    HERE_RESPAWN_FIXTURES,
    ids=[f.test_id for f in HERE_RESPAWN_FIXTURES],
)
def test_here_mode_respawn_provisioning(
    session: Session,
    tmp_path: pathlib.Path,
    test_id: str,
    start_directory: bool,
    environment: dict[str, str] | None,
    window_shell: str | None,
    expect_respawn: bool,
) -> None:
    """--here mode uses respawn-pane for provisioning, not send_keys."""
    test_dir = tmp_path / "here_respawn"
    test_dir.mkdir()

    workspace: dict[str, t.Any] = {
        "session_name": session.name,
        "windows": [
            {
                "window_name": "respawn-test",
                "panes": [{"shell_command": []}],
            },
        ],
    }
    if start_directory:
        workspace["windows"][0]["start_directory"] = str(test_dir)
    if environment:
        workspace["windows"][0]["environment"] = environment

    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)

    original_pane = session.active_window.active_pane
    assert original_pane is not None
    original_pid = original_pane.pane_pid

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    builder.build(session=session, here=True)

    pane = session.active_window.active_pane
    assert pane is not None

    if expect_respawn:
        # respawn-pane -k replaces the shell process, so PID changes
        assert pane.pane_pid != original_pid, (
            f"Expected new PID after respawn, got same: {pane.pane_pid}"
        )
    else:
        # No provisioning needed — pane process should be unchanged
        assert pane.pane_pid == original_pid

    if start_directory:
        expected_path = os.path.realpath(str(test_dir))
        assert retry_until(
            lambda: pane.pane_current_path == expected_path,
            seconds=5,
        ), f"Expected {expected_path}, got {pane.pane_current_path}"

    if environment:
        env = session.show_environment()
        for key, val in environment.items():
            assert env.get(key) == val


def test_here_mode_respawn_multiple_env_vars(
    session: Session,
) -> None:
    """--here mode sets multiple environment variables via set_environment."""
    workspace: dict[str, t.Any] = {
        "session_name": session.name,
        "windows": [
            {
                "window_name": "multi-env",
                "environment": {
                    "TMUXP_A": "alpha",
                    "TMUXP_B": "bravo",
                    "TMUXP_C": "charlie",
                },
                "panes": [{"shell_command": []}],
            },
        ],
    }
    workspace = loader.expand(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    builder.build(session=session, here=True)

    env = session.show_environment()
    assert env.get("TMUXP_A") == "alpha"
    assert env.get("TMUXP_B") == "bravo"
    assert env.get("TMUXP_C") == "charlie"


def test_here_mode_respawn_warns_on_running_processes(
    session: Session,
    caplog: pytest.LogCaptureFixture,
    tmp_path: pathlib.Path,
) -> None:
    """--here mode warns when respawn-pane will kill child processes."""
    # Start a background process in the active pane so pgrep finds children
    pane = session.active_window.active_pane
    assert pane is not None
    pane.send_keys("sleep 300 &", enter=True)

    # Give the shell time to fork the background job
    assert (
        retry_until(
            lambda: (
                "sleep" in (pane.pane_current_command or "")
                or retry_until(
                    lambda: len(pane.capture_pane()) > 1,
                    seconds=2,
                )
            ),
            seconds=3,
        )
        or True
    )  # Best-effort; pgrep check below is the real assertion

    test_dir = tmp_path / "warn_test"
    test_dir.mkdir()

    workspace: dict[str, t.Any] = {
        "session_name": session.name,
        "windows": [
            {
                "window_name": "warn-test",
                "start_directory": str(test_dir),
                "panes": [{"shell_command": []}],
            },
        ],
    }
    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)

    with caplog.at_level(logging.WARNING, logger="tmuxp.workspace.builder"):
        builder = WorkspaceBuilder(session_config=workspace, server=session.server)
        builder.build(session=session, here=True)

    warning_records = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING and "kill running processes" in r.message
    ]
    # pgrep should find the sleep background job and emit a warning
    assert len(warning_records) >= 1


def test_here_mode_no_warning_when_pane_idle(
    session: Session,
    caplog: pytest.LogCaptureFixture,
    tmp_path: pathlib.Path,
) -> None:
    """--here mode does not warn when pane has no child processes."""
    test_dir = tmp_path / "idle_test"
    test_dir.mkdir()

    workspace: dict[str, t.Any] = {
        "session_name": session.name,
        "windows": [
            {
                "window_name": "idle-test",
                "start_directory": str(test_dir),
                "panes": [{"shell_command": []}],
            },
        ],
    }
    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)

    with caplog.at_level(logging.WARNING, logger="tmuxp.workspace.builder"):
        builder = WorkspaceBuilder(session_config=workspace, server=session.server)
        builder.build(session=session, here=True)

    warning_records = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING and "kill running processes" in r.message
    ]
    assert len(warning_records) == 0


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

        with pytest.raises(libtmux.exc.LibTmuxException, match="no space for new pane"):
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
def test_pane_readiness_call_count(
    tmp_path: pathlib.Path,
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
    test_id: str,
    yaml: str,
    expected_wait_count: int,
) -> None:
    """Verify _wait_for_pane_ready is called only for appropriate panes."""
    call_count = 0
    original = builder_module._wait_for_pane_ready

    def counting_wait(
        pane: Pane,
        timeout: float = 2.0,
        interval: float = 0.05,
    ) -> bool:
        nonlocal call_count
        call_count += 1
        return original(pane, timeout=timeout, interval=interval)

    monkeypatch.setattr(builder_module, "_wait_for_pane_ready", counting_wait)

    yaml_workspace = tmp_path / "readiness.yaml"
    yaml_workspace.write_text(yaml, encoding="utf-8")
    workspace = ConfigReader._from_file(yaml_workspace)
    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=server)
    builder.build()
    assert call_count == expected_wait_count


def test_select_layout_not_called_after_yield(
    tmp_path: pathlib.Path,
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify select_layout is called once per pane, not duplicated in build()."""
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
    # 3 panes = 3 layout calls (one per pane in iter_create_panes), not 6
    assert call_count == 3


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


def test_on_project_exit_sets_hook(
    server: Server,
) -> None:
    """on_project_exit sets tmux client-detached hook on the session."""
    workspace: dict[str, t.Any] = {
        "session_name": "hook-exit-test",
        "on_project_exit": "echo goodbye",
        "windows": [{"window_name": "main", "panes": [{"shell_command": []}]}],
    }
    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=server)
    builder.build()

    hooks = builder.session.show_hooks()
    hook_keys = list(hooks.keys())
    assert any("client-detached" in k for k in hook_keys)

    builder.session.kill()


def test_on_project_exit_sets_hook_list(
    server: Server,
) -> None:
    """on_project_exit joins list commands and sets tmux hook."""
    workspace: dict[str, t.Any] = {
        "session_name": "hook-exit-list-test",
        "on_project_exit": ["echo a", "echo b"],
        "windows": [{"window_name": "main", "panes": [{"shell_command": []}]}],
    }
    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=server)
    builder.build()

    hooks = builder.session.show_hooks()
    hook_keys = list(hooks.keys())
    assert any("client-detached" in k for k in hook_keys)

    builder.session.kill()


def test_on_project_exit_hook_includes_cwd(
    server: Server,
) -> None:
    """on_project_exit hook includes cd to start_directory."""
    workspace: dict[str, t.Any] = {
        "session_name": "hook-exit-cwd-test",
        "start_directory": "/tmp",
        "on_project_exit": "echo goodbye",
        "windows": [{"window_name": "main", "panes": [{"shell_command": []}]}],
    }
    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=server)
    builder.build()

    hooks = builder.session.show_hooks()
    hook_values = list(hooks.values())
    matched = [v for v in hook_values if "cd" in str(v) and "/tmp" in str(v)]
    assert len(matched) >= 1

    builder.session.kill()


class OnProjectExitCwdSpecialFixture(t.NamedTuple):
    """Test fixture for on_project_exit hook with special cwd characters."""

    test_id: str
    dir_name: str
    expected_substring: str


ON_PROJECT_EXIT_CWD_SPECIAL_FIXTURES: list[OnProjectExitCwdSpecialFixture] = [
    OnProjectExitCwdSpecialFixture(
        test_id="spaces_in_path",
        dir_name="my project dir",
        expected_substring="my project dir",
    ),
    OnProjectExitCwdSpecialFixture(
        test_id="single_quote_in_path",
        dir_name="it's a project",
        expected_substring="a project",
    ),
]


@pytest.mark.parametrize(
    list(OnProjectExitCwdSpecialFixture._fields),
    ON_PROJECT_EXIT_CWD_SPECIAL_FIXTURES,
    ids=[f.test_id for f in ON_PROJECT_EXIT_CWD_SPECIAL_FIXTURES],
)
def test_on_project_exit_hook_cwd_special_chars(
    server: Server,
    tmp_path: pathlib.Path,
    test_id: str,
    dir_name: str,
    expected_substring: str,
) -> None:
    """on_project_exit hook correctly quotes start_directory with special chars."""
    special_dir = tmp_path / dir_name
    special_dir.mkdir()
    workspace: dict[str, t.Any] = {
        "session_name": f"hook-exit-{test_id}",
        "start_directory": str(special_dir),
        "on_project_exit": "echo goodbye",
        "windows": [{"window_name": "main", "panes": [{"shell_command": []}]}],
    }
    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=server)
    builder.build()

    hooks = builder.session.show_hooks()
    hook_values = [str(v) for v in hooks.values()]
    matched = [v for v in hook_values if expected_substring in v]
    assert len(matched) >= 1, (
        f"Expected {expected_substring!r} in hook values, got {hook_values}"
    )

    builder.session.kill()


def test_on_project_stop_sets_environment(
    server: Server,
) -> None:
    """on_project_stop stores commands in session environment."""
    workspace: dict[str, t.Any] = {
        "session_name": "hook-stop-env-test",
        "on_project_stop": "docker compose down",
        "windows": [{"window_name": "main", "panes": [{"shell_command": []}]}],
    }
    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=server)
    builder.build()

    stop_cmd = builder.session.getenv("TMUXP_ON_PROJECT_STOP")
    assert stop_cmd == "docker compose down"

    builder.session.kill()


def test_on_project_stop_sets_start_directory_env(
    server: Server,
    tmp_path: pathlib.Path,
) -> None:
    """build() stores start_directory in session environment."""
    workspace: dict[str, t.Any] = {
        "session_name": "hook-startdir-env-test",
        "start_directory": str(tmp_path),
        "windows": [{"window_name": "main", "panes": [{"shell_command": []}]}],
    }
    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=server)
    builder.build()

    start_dir = builder.session.getenv("TMUXP_START_DIRECTORY")
    assert start_dir == str(tmp_path)

    builder.session.kill()


def test_clear_sends_clear_to_panes(
    session: Session,
) -> None:
    """clear: true sends clear command to all panes after window creation."""
    workspace: dict[str, t.Any] = {
        "session_name": session.name,
        "windows": [
            {
                "window_name": "clear-test",
                "clear": True,
                "panes": [
                    {"shell_command": ["echo BEFORE_CLEAR"]},
                    {"shell_command": ["echo BEFORE_CLEAR"]},
                ],
            },
        ],
    }
    workspace = loader.expand(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    builder.build(session=session)

    window = session.windows[0]
    assert len(window.panes) == 2

    for pane in window.panes:

        def check(p: Pane = pane) -> bool:
            captured = "\n".join(p.capture_pane()).strip()
            return "BEFORE_CLEAR" not in captured

        assert retry_until(check, raises=False), (
            f"Expected BEFORE_CLEAR to be cleared from pane {pane.pane_id}"
        )


def test_clear_false_does_not_clear(
    session: Session,
) -> None:
    """clear: false does not clear pane content."""
    workspace: dict[str, t.Any] = {
        "session_name": session.name,
        "windows": [
            {
                "window_name": "no-clear-test",
                "clear": False,
                "panes": [
                    {"shell_command": ["echo SHOULD_REMAIN"]},
                ],
            },
        ],
    }
    workspace = loader.expand(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    builder.build(session=session)

    window = session.windows[0]
    pane = window.panes[0]

    def check(p: Pane = pane) -> bool:
        return "SHOULD_REMAIN" in "\n".join(p.capture_pane())

    assert retry_until(check), (
        f"Expected SHOULD_REMAIN to remain in pane {pane.pane_id}"
    )
