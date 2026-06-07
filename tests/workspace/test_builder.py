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


class SynchronizeBuilderFixture(t.NamedTuple):
    """Fixture for synchronize shorthand builder behavior."""

    test_id: str
    synchronize: bool | str
    expected_synchronized: bool | None


SYNCHRONIZE_BUILDER_FIXTURES: list[SynchronizeBuilderFixture] = [
    SynchronizeBuilderFixture(
        test_id="true",
        synchronize=True,
        expected_synchronized=True,
    ),
    SynchronizeBuilderFixture(
        test_id="before",
        synchronize="before",
        expected_synchronized=True,
    ),
    SynchronizeBuilderFixture(
        test_id="after",
        synchronize="after",
        expected_synchronized=True,
    ),
    SynchronizeBuilderFixture(
        test_id="false",
        synchronize=False,
        expected_synchronized=False,
    ),
]


@pytest.mark.parametrize(
    list(SynchronizeBuilderFixture._fields),
    SYNCHRONIZE_BUILDER_FIXTURES,
    ids=[fixture.test_id for fixture in SYNCHRONIZE_BUILDER_FIXTURES],
)
def test_synchronize_builder_options(
    session: Session,
    test_id: str,
    synchronize: bool | str,
    expected_synchronized: bool | None,
) -> None:
    """Synchronize shorthand sets synchronize-panes on the built window."""
    workspace: dict[str, t.Any] = {
        "session_name": f"sync-builder-{test_id}",
        "windows": [
            {
                "window_name": "main",
                "synchronize": synchronize,
                "panes": ["echo pane0", "echo pane1"],
            },
        ],
    }
    workspace = loader.expand(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    builder.build(session=session)

    assert session.windows[0].show_option("synchronize-panes") is expected_synchronized


class IteratorSynchronizeOptionFixture(t.NamedTuple):
    """Fixture for direct iterator synchronize-panes option behavior."""

    test_id: str
    option_value: str
    expected_synchronized: bool


ITERATOR_SYNCHRONIZE_OPTION_FIXTURES: list[IteratorSynchronizeOptionFixture] = [
    IteratorSynchronizeOptionFixture(
        test_id="on",
        option_value="on",
        expected_synchronized=True,
    ),
    IteratorSynchronizeOptionFixture(
        test_id="off",
        option_value="off",
        expected_synchronized=False,
    ),
]


@pytest.mark.parametrize(
    list(IteratorSynchronizeOptionFixture._fields),
    ITERATOR_SYNCHRONIZE_OPTION_FIXTURES,
    ids=[fixture.test_id for fixture in ITERATOR_SYNCHRONIZE_OPTION_FIXTURES],
)
def test_iter_create_windows_preserves_raw_synchronize_panes_option(
    session: Session,
    test_id: str,
    option_value: str,
    expected_synchronized: bool,
) -> None:
    """Direct iter_create_windows() calls apply raw synchronize-panes options."""
    workspace: dict[str, t.Any] = {
        "session_name": session.name,
        "windows": [
            {
                "window_name": f"iterator-sync-{test_id}",
                "options": {"synchronize-panes": option_value},
                "panes": ["echo pane0"],
            },
        ],
    }
    workspace = loader.expand(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    window, _window_config = next(builder.iter_create_windows(session=session))

    assert window.show_option("synchronize-panes") is expected_synchronized


class SyncIsolationFixture(t.NamedTuple):
    """Fixture for build-time synchronize-panes isolation."""

    test_id: str
    window_extra: dict[str, t.Any]
    global_synchronize: bool
    expected_local_sync: bool | None
    expected_effective_sync: bool


SYNC_ISOLATION_FIXTURES: list[SyncIsolationFixture] = [
    SyncIsolationFixture(
        test_id="sync_before",
        window_extra={"synchronize": "before"},
        global_synchronize=False,
        expected_local_sync=True,
        expected_effective_sync=True,
    ),
    SyncIsolationFixture(
        test_id="sync_true",
        window_extra={"synchronize": True},
        global_synchronize=False,
        expected_local_sync=True,
        expected_effective_sync=True,
    ),
    SyncIsolationFixture(
        test_id="sync_after",
        window_extra={"synchronize": "after"},
        global_synchronize=False,
        expected_local_sync=True,
        expected_effective_sync=True,
    ),
    SyncIsolationFixture(
        test_id="explicit_options_on",
        window_extra={"options": {"synchronize-panes": "on"}},
        global_synchronize=False,
        expected_local_sync=True,
        expected_effective_sync=True,
    ),
    SyncIsolationFixture(
        test_id="explicit_options_after_on",
        window_extra={"options_after": {"synchronize-panes": "on"}},
        global_synchronize=False,
        expected_local_sync=True,
        expected_effective_sync=True,
    ),
    SyncIsolationFixture(
        test_id="inherits_global_on",
        window_extra={},
        global_synchronize=True,
        expected_local_sync=None,
        expected_effective_sync=True,
    ),
    SyncIsolationFixture(
        test_id="sync_false_overrides_global_on",
        window_extra={"synchronize": False},
        global_synchronize=True,
        expected_local_sync=False,
        expected_effective_sync=False,
    ),
]


@pytest.mark.parametrize(
    list(SyncIsolationFixture._fields),
    SYNC_ISOLATION_FIXTURES,
    ids=[fixture.test_id for fixture in SYNC_ISOLATION_FIXTURES],
)
def test_synchronize_keeps_setup_commands_isolated(
    session: Session,
    test_id: str,
    window_extra: dict[str, t.Any],
    global_synchronize: bool,
    expected_local_sync: bool | None,
    expected_effective_sync: bool,
) -> None:
    """Pane setup commands are never broadcast while a window is building."""
    if global_synchronize:
        session.server.cmd("set-window-option", "-g", "synchronize-panes", "on")

    window_config: dict[str, t.Any] = {
        "window_name": f"sync-isolated-{test_id}",
        "panes": [
            "printf '__PANE0__\\n'",
            "printf '__PANE1__\\n'",
        ],
    }
    window_config.update(window_extra)
    workspace: dict[str, t.Any] = {
        "session_name": session.name,
        "windows": [window_config],
    }
    workspace = loader.expand(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    builder.build(session=session)

    window = session.windows[0]
    panes = window.panes

    def output_lines(pane: Pane, marker: str) -> int:
        return sum(1 for line in pane.capture_pane() if line.strip() == marker)

    def setup_complete() -> bool:
        return (
            output_lines(panes[0], "__PANE0__") >= 1
            and output_lines(panes[1], "__PANE1__") >= 1
        )

    assert retry_until(setup_complete), "Expected setup markers in their own panes"
    assert output_lines(panes[0], "__PANE1__") == 0
    assert output_lines(panes[1], "__PANE0__") == 0
    assert window.show_option("synchronize-panes") is expected_local_sync
    assert (
        window.show_option("synchronize-panes", include_inherited=True)
        is expected_effective_sync
    )


def test_synchronize_preserves_plugin_final_state(session: Session) -> None:
    """Plugin-set synchronize-panes is restored after isolated setup."""

    class SyncOnWindowCreatePlugin:
        """Plugin that chooses synchronized panes as the final window state."""

        def before_workspace_builder(self, session: Session) -> None:
            """No-op workspace hook."""

        def on_window_create(self, window: Window) -> None:
            """Set the final synchronized state before pane setup starts."""
            window.set_option("synchronize-panes", True)

        def after_window_finished(self, window: Window) -> None:
            """No-op window hook."""

    workspace: dict[str, t.Any] = {
        "session_name": session.name,
        "windows": [
            {
                "window_name": "sync-plugin-final",
                "panes": [
                    "printf '__PANE0__\\n'",
                    "printf '__PANE1__\\n'",
                ],
            },
        ],
    }
    workspace = loader.expand(workspace)

    builder = WorkspaceBuilder(
        session_config=workspace,
        server=session.server,
        plugins=[SyncOnWindowCreatePlugin()],
    )
    builder.build(session=session)

    window = session.windows[0]
    panes = window.panes

    def output_lines(pane: Pane, marker: str) -> int:
        return sum(1 for line in pane.capture_pane() if line.strip() == marker)

    def setup_complete() -> bool:
        return (
            output_lines(panes[0], "__PANE0__") >= 1
            and output_lines(panes[1], "__PANE1__") >= 1
        )

    assert retry_until(setup_complete), "Expected setup markers in their own panes"
    assert output_lines(panes[0], "__PANE1__") == 0
    assert output_lines(panes[1], "__PANE0__") == 0
    assert window.show_option("synchronize-panes") is True


class SyncFanoutFixture(t.NamedTuple):
    """Fixture for shell_command_after under synchronize-panes modes."""

    test_id: str
    window_extra: dict[str, t.Any]


SYNC_FANOUT_FIXTURES: list[SyncFanoutFixture] = [
    SyncFanoutFixture(test_id="sync_after", window_extra={"synchronize": "after"}),
    SyncFanoutFixture(test_id="sync_before", window_extra={"synchronize": "before"}),
    SyncFanoutFixture(test_id="sync_true", window_extra={"synchronize": True}),
    SyncFanoutFixture(
        test_id="explicit_option",
        window_extra={"options": {"synchronize-panes": "on"}},
    ),
]


@pytest.mark.parametrize(
    list(SyncFanoutFixture._fields),
    SYNC_FANOUT_FIXTURES,
    ids=[fixture.test_id for fixture in SYNC_FANOUT_FIXTURES],
)
def test_shell_command_after_runs_once_per_pane_when_synchronized(
    session: Session,
    test_id: str,
    window_extra: dict[str, t.Any],
) -> None:
    """shell_command_after runs exactly once per pane in every sync mode.

    tmuxp keeps synchronize-panes off while it sends post-build commands,
    then restores the final configured synchronize-panes state afterward.
    """
    window_config: dict[str, t.Any] = {
        "window_name": f"sync-cmds-{test_id}",
        "shell_command_after": [
            "echo __SYNC_AF''TER__",
            "echo __SYNC_DO''NE__",
        ],
        "panes": ["echo pane0", "echo pane1"],
    }
    window_config.update(window_extra)
    workspace: dict[str, t.Any] = {
        "session_name": session.name,
        "windows": [window_config],
    }
    workspace = loader.expand(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    builder.build(session=session)

    window = session.windows[0]
    assert window.show_option("synchronize-panes") is True

    def output_lines(pane: Pane, marker: str) -> int:
        return sum(1 for line in pane.capture_pane() if line.strip() == marker)

    for pane in window.panes:

        def done(p: Pane = pane) -> bool:
            return output_lines(p, "__SYNC_DONE__") >= 1

        assert retry_until(done), f"Expected __SYNC_DONE__ in pane {pane.pane_id}"
        count = output_lines(pane, "__SYNC_AFTER__")
        assert count == 1, (
            f"Pane {pane.pane_id} ran shell_command_after {count} times; "
            "synchronize-panes was enabled before the fan-out"
        )


def test_pane_titles(
    session: Session,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Pane title config sets pane-border options and pane titles."""
    workspace: dict[str, t.Any] = {
        "session_name": session.name,
        "enable_pane_titles": True,
        "windows": [
            {
                "window_name": "titled",
                "panes": [
                    {"title": "editor", "shell_command": ["echo pane0"]},
                    {"title": "runner", "shell_command": ["echo pane1"]},
                    {"title": "", "shell_command": ["echo pane2"]},
                    {"shell_command": ["echo pane3"]},
                ],
            },
        ],
    }
    workspace = loader.expand(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    with caplog.at_level(logging.WARNING, logger="tmuxp.workspace.builder"):
        builder.build(session=session)

    window = session.windows[0]
    assert window.show_option("pane-border-status") == "top"
    assert window.show_option("pane-border-format") == "#{pane_index}: #{pane_title}"

    panes = window.panes
    assert len(panes) == 4

    def check_title(pane: Pane, expected: str) -> bool:
        pane.refresh()
        return pane.pane_title == expected

    assert retry_until(functools.partial(check_title, panes[0], "editor")), (
        f"Expected title 'editor', got {panes[0].pane_title!r}"
    )
    assert retry_until(functools.partial(check_title, panes[1], "runner")), (
        f"Expected title 'runner', got {panes[1].pane_title!r}"
    )

    # tmux discards empty titles; an explicit title: "" warns instead
    blank_warnings = [
        record
        for record in caplog.records
        if record.levelno == logging.WARNING and hasattr(record, "tmux_pane")
    ]
    assert len(blank_warnings) == 1
    assert blank_warnings[0].tmux_pane == panes[2].pane_id


class ClearBuilderFixture(t.NamedTuple):
    """Fixture for clear window behavior."""

    test_id: str
    clear: bool
    marker_should_remain: bool


CLEAR_BUILDER_FIXTURES: list[ClearBuilderFixture] = [
    ClearBuilderFixture(
        test_id="clear-true",
        clear=True,
        marker_should_remain=False,
    ),
    ClearBuilderFixture(
        test_id="clear-false",
        clear=False,
        marker_should_remain=True,
    ),
]


@pytest.mark.parametrize(
    list(ClearBuilderFixture._fields),
    CLEAR_BUILDER_FIXTURES,
    ids=[fixture.test_id for fixture in CLEAR_BUILDER_FIXTURES],
)
def test_clear_window(
    session: Session,
    test_id: str,
    clear: bool,
    marker_should_remain: bool,
) -> None:
    """Clear sends clear to panes only when enabled."""
    marker = f"__{test_id.upper().replace('-', '_')}__"
    workspace: dict[str, t.Any] = {
        "session_name": session.name,
        "windows": [
            {
                "window_name": "clear-test",
                "clear": clear,
                "panes": [{"shell_command": [f"echo {marker}"]}],
            },
        ],
    }
    workspace = loader.expand(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    builder.build(session=session)

    pane = session.windows[0].panes[0]

    def marker_visible() -> bool:
        return marker in "\n".join(pane.capture_pane())

    if marker_should_remain:
        assert retry_until(marker_visible)
    else:

        def marker_cleared() -> bool:
            return not marker_visible()

        assert retry_until(marker_cleared, raises=False)


class PostBuildSuppressHistoryFixture(t.NamedTuple):
    """Fixture for post-build suppress_history behavior."""

    test_id: str
    suppress_history: bool | None
    expected_suppress_history: bool


POST_BUILD_SUPPRESS_HISTORY_FIXTURES: list[PostBuildSuppressHistoryFixture] = [
    PostBuildSuppressHistoryFixture(
        test_id="default",
        suppress_history=None,
        expected_suppress_history=True,
    ),
    PostBuildSuppressHistoryFixture(
        test_id="explicit-false",
        suppress_history=False,
        expected_suppress_history=False,
    ),
]


@pytest.mark.parametrize(
    list(PostBuildSuppressHistoryFixture._fields),
    POST_BUILD_SUPPRESS_HISTORY_FIXTURES,
    ids=[fixture.test_id for fixture in POST_BUILD_SUPPRESS_HISTORY_FIXTURES],
)
def test_post_build_commands_honor_suppress_history(
    session: Session,
    monkeypatch: pytest.MonkeyPatch,
    test_id: str,
    suppress_history: bool | None,
    expected_suppress_history: bool,
) -> None:
    """Post-build commands use the window suppress_history setting."""
    sent: list[tuple[str | None, bool | None]] = []
    original_send_keys = Pane.send_keys

    def spy_send_keys(
        self: Pane,
        cmd: str | None = None,
        enter: bool | None = True,
        suppress_history: bool | None = False,
        literal: bool | None = False,
        reset: bool | None = None,
        copy_mode_cmd: str | None = None,
        repeat: int | None = None,
        expand_formats: bool | None = None,
        hex_keys: bool | None = None,
        target_client: str | None = None,
        key_name: bool | None = None,
    ) -> None:
        sent.append((cmd, suppress_history))
        original_send_keys(
            self,
            cmd=cmd,
            enter=enter,
            suppress_history=suppress_history,
            literal=literal,
            reset=reset,
            copy_mode_cmd=copy_mode_cmd,
            repeat=repeat,
            expand_formats=expand_formats,
            hex_keys=hex_keys,
            target_client=target_client,
            key_name=key_name,
        )

    monkeypatch.setattr(Pane, "send_keys", spy_send_keys)

    window_config: dict[str, t.Any] = {
        "window_name": f"post-build-history-{test_id}",
        "shell_command_after": ["echo __POST_BUILD_AFTER__"],
        "clear": True,
        "panes": ["echo pane"],
    }
    if suppress_history is not None:
        window_config["suppress_history"] = suppress_history

    workspace: dict[str, t.Any] = {
        "session_name": session.name,
        "windows": [window_config],
    }
    workspace = loader.expand(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    builder.build(session=session)

    assert ("echo __POST_BUILD_AFTER__", expected_suppress_history) in sent
    assert ("clear", expected_suppress_history) in sent


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


class AfterCommandOptionsFixture(t.NamedTuple):
    """Fixture for per-command options in shell_command_after mappings."""

    test_id: str
    command: dict[str, t.Any]
    expected_enter: bool
    expected_sleeps: list[float]


AFTER_COMMAND_OPTIONS_FIXTURES: list[AfterCommandOptionsFixture] = [
    AfterCommandOptionsFixture(
        test_id="enter_false_respected",
        command={"cmd": "echo __AFTER_OPT__", "enter": False},
        expected_enter=False,
        expected_sleeps=[],
    ),
    AfterCommandOptionsFixture(
        test_id="sleeps_once_per_wave",
        command={
            "cmd": "echo __AFTER_OPT__",
            "sleep_before": 0.21,
            "sleep_after": 0.31,
        },
        expected_enter=True,
        expected_sleeps=[0.21, 0.31],
    ),
]


@pytest.mark.parametrize(
    list(AfterCommandOptionsFixture._fields),
    AFTER_COMMAND_OPTIONS_FIXTURES,
    ids=[fixture.test_id for fixture in AFTER_COMMAND_OPTIONS_FIXTURES],
)
def test_shell_command_after_honors_command_options(
    session: Session,
    monkeypatch: pytest.MonkeyPatch,
    test_id: str,
    command: dict[str, t.Any],
    expected_enter: bool,
    expected_sleeps: list[float],
) -> None:
    """shell_command_after mappings keep their enter and sleep options.

    The pane command loop honors per-command enter/sleep_before/
    sleep_after; the post-build fan-out accepts the same mapping syntax
    and must behave the same. Sleeps apply once per command wave, not
    once per pane.
    """
    sent: list[tuple[str | None, bool | None]] = []
    original_send_keys = Pane.send_keys

    def spy_send_keys(
        self: Pane,
        cmd: str | None = None,
        enter: bool | None = True,
        suppress_history: bool | None = False,
        literal: bool | None = False,
        reset: bool | None = None,
        copy_mode_cmd: str | None = None,
        repeat: int | None = None,
        expand_formats: bool | None = None,
        hex_keys: bool | None = None,
        target_client: str | None = None,
        key_name: bool | None = None,
    ) -> None:
        sent.append((cmd, enter))
        original_send_keys(
            self,
            cmd=cmd,
            enter=enter,
            suppress_history=suppress_history,
            literal=literal,
            reset=reset,
            copy_mode_cmd=copy_mode_cmd,
            repeat=repeat,
            expand_formats=expand_formats,
            hex_keys=hex_keys,
            target_client=target_client,
            key_name=key_name,
        )

    monkeypatch.setattr(Pane, "send_keys", spy_send_keys)

    slept: list[float] = []
    original_sleep = time.sleep

    def spy_sleep(seconds: float) -> None:
        slept.append(seconds)
        original_sleep(0)

    monkeypatch.setattr("tmuxp.workspace.builder.time.sleep", spy_sleep)

    workspace: dict[str, t.Any] = {
        "session_name": session.name,
        "windows": [
            {
                "window_name": f"after-options-{test_id}",
                "shell_command_after": [command],
                "panes": ["echo pane0", "echo pane1"],
            },
        ],
    }
    workspace = loader.expand(workspace)

    builder = WorkspaceBuilder(session_config=workspace, server=session.server)
    builder.build(session=session)

    after_sends = [entry for entry in sent if entry[0] == "echo __AFTER_OPT__"]
    assert len(after_sends) == 2, "after-command should reach both panes"
    assert all(enter is expected_enter for _, enter in after_sends)

    option_sleeps = [s for s in slept if s in (0.21, 0.31)]
    assert sorted(option_sleeps) == sorted(expected_sleeps)
