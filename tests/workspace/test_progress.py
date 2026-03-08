"""Tests for tmuxp workspace builder progress callback."""

from __future__ import annotations

import typing as t

import pytest
from libtmux.server import Server

from tmuxp import exc
from tmuxp.workspace.builder import WorkspaceBuilder


def test_builder_on_progress_callback(
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """WorkspaceBuilder calls on_progress at each build milestone."""
    monkeypatch.delenv("TMUX", raising=False)

    session_config = {
        "session_name": "progress-test",
        "windows": [{"window_name": "editor", "panes": [{"shell_command": []}]}],
    }

    calls: list[str] = []
    builder = WorkspaceBuilder(
        session_config=session_config,
        server=server,
        on_progress=calls.append,
    )
    builder.build()

    assert any("Session created:" in c for c in calls)
    assert any("Creating window:" in c for c in calls)
    assert any("Creating pane:" in c for c in calls)
    assert "Workspace built" in calls


def test_builder_on_before_script_not_called_without_script(
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """on_before_script callback is not invoked when config has no before_script key."""
    monkeypatch.delenv("TMUX", raising=False)

    session_config = {
        "session_name": "no-script-callback-test",
        "windows": [{"window_name": "main", "panes": [{"shell_command": []}]}],
    }
    called: list[bool] = []
    builder = WorkspaceBuilder(
        session_config=session_config,
        server=server,
        on_before_script=lambda: called.append(True),
    )
    builder.build()
    assert called == []


def test_builder_on_script_output_not_called_without_script(
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """on_script_output callback is not invoked when config has no before_script key."""
    monkeypatch.delenv("TMUX", raising=False)

    session_config = {
        "session_name": "no-script-output-test",
        "windows": [{"window_name": "main", "panes": [{"shell_command": []}]}],
    }
    lines: list[str] = []
    builder = WorkspaceBuilder(
        session_config=session_config,
        server=server,
        on_script_output=lines.append,
    )
    builder.build()
    assert lines == []


def test_builder_on_build_event_sequence(
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """on_build_event fires the full event sequence during build()."""
    monkeypatch.delenv("TMUX", raising=False)

    session_config = {
        "session_name": "build-event-test",
        "windows": [
            {
                "window_name": "editor",
                "panes": [{"shell_command": []}, {"shell_command": []}],
            },
            {"window_name": "logs", "panes": [{"shell_command": []}]},
        ],
    }
    events: list[dict[str, t.Any]] = []
    builder = WorkspaceBuilder(
        session_config=session_config,
        server=server,
        on_build_event=events.append,
    )
    builder.build()

    event_types = [e["event"] for e in events]
    assert event_types[0] == "session_created"
    assert event_types[-1] == "workspace_built"
    assert event_types.count("window_started") == 2
    assert event_types.count("window_done") == 2
    assert event_types.count("pane_creating") == 3  # 2 panes + 1 pane

    created = next(e for e in events if e["event"] == "session_created")
    assert created["window_total"] == 2
    assert created["session_pane_total"] == 3  # 2 panes + 1 pane


def test_builder_on_build_event_session_name(
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """session_created event carries correct session name."""
    monkeypatch.delenv("TMUX", raising=False)

    session_config = {
        "session_name": "name-check",
        "windows": [{"window_name": "main", "panes": [{"shell_command": []}]}],
    }
    events: list[dict[str, t.Any]] = []
    builder = WorkspaceBuilder(
        session_config=session_config,
        server=server,
        on_build_event=events.append,
    )
    builder.build()

    created = next(e for e in events if e["event"] == "session_created")
    assert created["name"] == "name-check"
    assert created["window_total"] == 1


def test_builder_on_build_event_session_pane_total(
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """session_created event includes session_pane_total summing all windows' panes."""
    monkeypatch.delenv("TMUX", raising=False)

    pane: dict[str, list[object]] = {"shell_command": []}
    session_config = {
        "session_name": "pane-total-test",
        "windows": [
            {"window_name": "w1", "panes": [pane, pane]},
            {"window_name": "w2", "panes": [pane]},
            {"window_name": "w3", "panes": [pane, pane, pane]},
        ],
    }
    events: list[dict[str, t.Any]] = []
    builder = WorkspaceBuilder(
        session_config=session_config,
        server=server,
        on_build_event=events.append,
    )
    builder.build()

    created = next(e for e in events if e["event"] == "session_created")
    assert created["session_pane_total"] == 6  # 2 + 1 + 3


def test_builder_before_script_events(
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """before_script_started fires before run; before_script_done fires in finally."""
    monkeypatch.delenv("TMUX", raising=False)

    session_config = {
        "session_name": "before-script-events-test",
        "before_script": "echo hello",
        "windows": [{"window_name": "main", "panes": [{"shell_command": []}]}],
    }
    events: list[dict[str, t.Any]] = []
    builder = WorkspaceBuilder(
        session_config=session_config,
        server=server,
        on_build_event=events.append,
    )
    builder.build()

    event_types = [e["event"] for e in events]
    assert "before_script_started" in event_types
    assert "before_script_done" in event_types

    bs_start_idx = event_types.index("before_script_started")
    bs_done_idx = event_types.index("before_script_done")
    win_idx = event_types.index("window_started")
    assert bs_start_idx < bs_done_idx < win_idx


def test_builder_before_script_done_fires_on_failure(
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """before_script_done fires in finally even when the script fails."""
    monkeypatch.delenv("TMUX", raising=False)

    session_config = {
        "session_name": "before-script-fail-test",
        "before_script": "/bin/false",
        "windows": [{"window_name": "main", "panes": [{"shell_command": []}]}],
    }
    events: list[dict[str, t.Any]] = []
    builder = WorkspaceBuilder(
        session_config=session_config,
        server=server,
        on_build_event=events.append,
    )
    with pytest.raises(exc.BeforeLoadScriptError):
        builder.build()

    event_types = [e["event"] for e in events]
    assert "before_script_started" in event_types
    assert "before_script_done" in event_types


def test_builder_on_build_event_pane_numbers(
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """pane_creating events carry 1-based pane_num and correct pane_total."""
    monkeypatch.delenv("TMUX", raising=False)

    session_config = {
        "session_name": "pane-num-test",
        "windows": [
            {
                "window_name": "main",
                "panes": [
                    {"shell_command": []},
                    {"shell_command": []},
                    {"shell_command": []},
                ],
            },
        ],
    }
    events: list[dict[str, t.Any]] = []
    builder = WorkspaceBuilder(
        session_config=session_config,
        server=server,
        on_build_event=events.append,
    )
    builder.build()

    pane_events = [e for e in events if e["event"] == "pane_creating"]
    assert len(pane_events) == 3
    assert [e["pane_num"] for e in pane_events] == [1, 2, 3]
    assert all(e["pane_total"] == 3 for e in pane_events)
