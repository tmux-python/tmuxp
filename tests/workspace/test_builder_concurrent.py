"""Tests for the concurrent workspace builder.

Covers :class:`tmuxp.workspace.builder.concurrent.ConcurrentWorkspaceBuilder`:
multi-pane / multi-window builds, command dispatch, single-pass layout, the
``pane_readiness`` policy, many-pane space reclaim, and the sequential fallback
for ``start_directory`` dependencies.
"""

from __future__ import annotations

import functools
import typing as t

import pytest
from libtmux.exc import LibTmuxException
from libtmux.pane import Pane
from libtmux.session import Session
from libtmux.test.retry import retry_until
from libtmux.window import Window

from tests.fixtures import utils as test_utils
from tmuxp._internal.config_reader import ConfigReader
from tmuxp.workspace import loader
from tmuxp.workspace.builder import concurrent as builder_concurrent, registry
from tmuxp.workspace.builder.concurrent import ConcurrentWorkspaceBuilder

if t.TYPE_CHECKING:
    import pathlib
    from collections.abc import Iterator

    from libtmux.server import Server


def _expand(config: dict[str, t.Any]) -> dict[str, t.Any]:
    """Run a raw workspace dict through the load pipeline (expand + trickle)."""
    return loader.trickle(loader.expand(config))


def test_concurrent_entry_point_resolves() -> None:
    """The 'concurrent' entry point resolves to the concurrent builder."""
    resolved = registry.resolve_builder_class({"workspace_builder": "concurrent"})
    assert resolved is ConcurrentWorkspaceBuilder


def test_concurrent_in_available_builders() -> None:
    """The concurrent entry point is discoverable."""
    assert "concurrent" in registry.available_builders()


def test_concurrent_builds_multiple_windows_and_panes(server: Server) -> None:
    """A multi-window, multi-pane workspace builds through the registry."""
    config = _expand(
        {
            "session_name": "concurrent-multi",
            "workspace_builder": "concurrent",
            "windows": [
                {
                    "window_name": "editor",
                    "panes": [{"shell_command": []}, {"shell_command": []}],
                },
                {
                    "window_name": "logs",
                    "panes": [
                        {"shell_command": []},
                        {"shell_command": []},
                        {"shell_command": []},
                    ],
                },
            ],
        },
    )
    builder_cls = registry.resolve_builder_class(config)
    builder = builder_cls(session_config=config, server=server)
    builder.build()
    try:
        assert builder.session.name == "concurrent-multi"
        windows = builder.session.windows
        assert sorted(w.name or "" for w in windows) == ["editor", "logs"]
        by_name = {w.name: w for w in windows}
        assert len(by_name["editor"].panes) == 2
        assert len(by_name["logs"].panes) == 3
    finally:
        builder.session.kill()


def test_concurrent_commands_land(server: Server) -> None:
    """Commands configured for each pane are sent to the shells."""
    marker_one = "__concurrent_pane_one__"
    marker_two = "__concurrent_pane_two__"
    config = _expand(
        {
            "session_name": "concurrent-commands",
            "workspace_builder": "concurrent",
            "windows": [
                {
                    "window_name": "main",
                    "panes": [
                        {"shell_command": [f"echo {marker_one}"]},
                        {"shell_command": [f"echo {marker_two}"]},
                    ],
                },
            ],
        },
    )
    builder = ConcurrentWorkspaceBuilder(session_config=config, server=server)
    builder.build()
    try:
        window = builder.session.windows[0]
        panes = window.panes
        assert len(panes) == 2

        def pane_shows(pane: Pane, marker: str) -> bool:
            return any(marker in line for line in pane.capture_pane())

        assert retry_until(functools.partial(pane_shows, panes[0], marker_one))
        assert retry_until(functools.partial(pane_shows, panes[1], marker_two))
    finally:
        builder.session.kill()


def test_concurrent_applies_layout_once(
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The configured layout is applied exactly once per window."""
    layout_calls: list[str | None] = []
    original_select_layout = Window.select_layout

    def counting_layout(self: Window, layout: str | None = None) -> Window:
        layout_calls.append(layout)
        return original_select_layout(self, layout)

    monkeypatch.setattr(Window, "select_layout", counting_layout)

    config = _expand(
        {
            "session_name": "concurrent-layout",
            "workspace_builder": "concurrent",
            "windows": [
                {
                    "window_name": "main",
                    "layout": "main-vertical",
                    "panes": [{"shell_command": []}, {"shell_command": []}],
                },
            ],
        },
    )
    builder = ConcurrentWorkspaceBuilder(session_config=config, server=server)
    builder.build()
    try:
        assert layout_calls == ["main-vertical"]
        assert len(builder.session.windows[0].panes) == 2
    finally:
        builder.session.kill()


class ReadinessCase(t.NamedTuple):
    """Pane-readiness barrier policy fixture."""

    test_id: str
    policy: str
    expected_barrier_calls: int


READINESS_CASES: list[ReadinessCase] = [
    ReadinessCase(
        test_id="never_skips_barrier",
        policy="never",
        expected_barrier_calls=0,
    ),
    ReadinessCase(
        test_id="always_runs_barrier",
        policy="always",
        expected_barrier_calls=1,
    ),
]


@pytest.mark.parametrize(
    list(ReadinessCase._fields),
    READINESS_CASES,
    ids=[c.test_id for c in READINESS_CASES],
)
def test_concurrent_pane_readiness_honored(
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
    test_id: str,
    policy: str,
    expected_barrier_calls: int,
) -> None:
    """``pane_readiness`` gates the concurrent readiness barrier."""
    calls = 0
    original = builder_concurrent._wait_for_panes_ready

    def counting(
        panes: list[Pane],
        timeout: float = 2.0,
        interval: float = 0.01,
    ) -> dict[str, bool]:
        nonlocal calls
        calls += 1
        return original(panes, timeout=timeout, interval=interval)

    monkeypatch.setattr(builder_concurrent, "_wait_for_panes_ready", counting)

    config = _expand(
        {
            "session_name": "concurrent-readiness",
            "workspace_builder": "concurrent",
            "workspace_builder_options": {"pane_readiness": policy},
            "windows": [
                {
                    "window_name": "main",
                    "panes": [{"shell_command": []}, {"shell_command": []}],
                },
            ],
        },
    )
    builder = ConcurrentWorkspaceBuilder(session_config=config, server=server)
    builder.build()
    try:
        assert calls == expected_barrier_calls
    finally:
        builder.session.kill()


class ReclaimCase(t.NamedTuple):
    """Reclaim-retry exception-matching fixture."""

    test_id: str
    error_message: str
    expect_reclaim: bool


RECLAIM_CASES: list[ReclaimCase] = [
    ReclaimCase(
        test_id="no_space_reclaims",
        error_message="no space for new pane",
        expect_reclaim=True,
    ),
    ReclaimCase(
        test_id="other_error_propagates",
        error_message="some other tmux failure",
        expect_reclaim=False,
    ),
]


@pytest.mark.parametrize(
    list(ReclaimCase._fields),
    RECLAIM_CASES,
    ids=[c.test_id for c in RECLAIM_CASES],
)
def test_concurrent_split_reclaims_only_on_no_space(
    session: Session,
    monkeypatch: pytest.MonkeyPatch,
    test_id: str,
    error_message: str,
    expect_reclaim: bool,
) -> None:
    """Reclaim retry runs only when a split fails for lack of space."""
    builder = ConcurrentWorkspaceBuilder(
        session_config={"session_name": "x", "windows": []},
        server=session.server,
    )
    window = session.active_window
    pane = window.active_pane
    assert pane is not None

    layout_calls: list[str | None] = []
    monkeypatch.setattr(
        Window,
        "select_layout",
        lambda self, layout=None: layout_calls.append(layout),
    )

    def failing_split(self: Pane, *args: t.Any, **kwargs: t.Any) -> Pane:
        raise LibTmuxException(error_message)

    monkeypatch.setattr(Pane, "split", failing_split)

    with pytest.raises(LibTmuxException, match=error_message):
        builder._split_pane_reclaiming_space(
            window,
            pane,
            {"attach": True},
            "tiled",
            [],
        )

    assert bool(layout_calls) == expect_reclaim


def test_concurrent_builds_many_panes_reclaiming_space(
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A window with many panes and a layout builds, reclaiming space as needed."""
    # Give the session room: the seven-pane fixture cannot fit in the 80x24
    # fallback, so back-to-back splitting relies on layout reclaim to make room.
    monkeypatch.setenv("COLUMNS", "200")
    monkeypatch.setenv("ROWS", "50")

    workspace = ConfigReader._from_file(
        test_utils.get_workspace_file(
            "regressions/issue_800_default_size_many_windows.yaml",
        ),
    )
    workspace["workspace_builder"] = "concurrent"
    workspace = loader.expand(workspace)
    workspace = loader.trickle(workspace)

    builder = ConcurrentWorkspaceBuilder(session_config=workspace, server=server)
    builder.build()
    try:
        assert len(server.sessions) == 1
        window = builder.session.windows[0]
        assert len(window.panes) == 7
    finally:
        builder.session.kill()


def test_concurrent_sequential_start_directory_dependency(
    server: Server,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A later pane's missing start_directory routes through the sequential path."""
    created_dir = tmp_path / "made_by_first_pane"
    assert not created_dir.exists()

    config = _expand(
        {
            "session_name": "concurrent-seq",
            "workspace_builder": "concurrent",
            "windows": [
                {
                    "window_name": "main",
                    "panes": [
                        {
                            "shell_command": [f"mkdir -p {created_dir}"],
                            "sleep_after": 0.5,
                        },
                        {
                            "start_directory": str(created_dir),
                            "shell_command": [],
                        },
                    ],
                },
            ],
        },
    )
    builder = ConcurrentWorkspaceBuilder(session_config=config, server=server)

    sequential_used = False
    eager_used = False
    original_seq = builder._iter_create_panes_sequentially
    original_eager = builder._create_window_panes

    def spy_seq(
        window: Window,
        window_config: dict[str, t.Any],
    ) -> Iterator[t.Any]:
        nonlocal sequential_used
        sequential_used = True
        yield from original_seq(window, window_config)

    def spy_eager(
        window: Window,
        window_config: dict[str, t.Any],
    ) -> list[t.Any]:
        nonlocal eager_used
        eager_used = True
        return original_eager(window, window_config)

    monkeypatch.setattr(builder, "_iter_create_panes_sequentially", spy_seq)
    monkeypatch.setattr(builder, "_create_window_panes", spy_eager)

    builder.build()
    try:
        assert sequential_used is True
        assert eager_used is False

        window = builder.session.windows[0]
        assert len(window.panes) == 2
        dependent_pane = window.panes[1]

        def in_created_dir() -> bool:
            path = dependent_pane.pane_current_path
            return path is not None and str(created_dir) in path

        assert retry_until(in_created_dir)
    finally:
        builder.session.kill()
