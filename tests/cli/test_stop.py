"""CLI tests for tmuxp stop."""

from __future__ import annotations

import argparse
import pathlib

import pytest
from libtmux.server import Server

from tmuxp.cli.stop import CLIStopNamespace, command_stop, create_stop_subparser


def _stop_args(
    server: Server,
    session_name: str | None,
) -> CLIStopNamespace:
    args = CLIStopNamespace()
    args.color = "never"
    args.session_name = session_name
    args.socket_name = server.socket_name
    args.socket_path = None
    return args


def test_create_stop_subparser() -> None:
    """create_stop_subparser() parses an optional session name."""
    parser = create_stop_subparser(argparse.ArgumentParser())

    args = parser.parse_args(["mysession"])

    assert args.session_name == "mysession"


def test_command_stop_kills_named_session(
    server: Server,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """command_stop() kills a named tmux session."""
    session = server.new_session(session_name="stop-named")

    command_stop(_stop_args(server, session.name))

    assert server.sessions.get(session_name="stop-named", default=None) is None
    assert "Stopped stop-named" in capsys.readouterr().out


def test_command_stop_runs_on_project_stop(
    tmp_path: pathlib.Path,
    server: Server,
) -> None:
    """command_stop() runs on_project_stop before killing the session."""
    marker = tmp_path / "stop-hook-ran"
    session = server.new_session(session_name="stop-hook")
    session.set_environment("TMUXP_ON_PROJECT_STOP", f"touch {marker}")
    session.set_environment("TMUXP_START_DIRECTORY", str(tmp_path))

    command_stop(_stop_args(server, session.name))

    assert marker.exists()
    assert server.sessions.get(session_name="stop-hook", default=None) is None


def test_command_stop_current_session_inside_tmux(
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """command_stop() stops the current tmux session when no name is given."""
    session = server.new_session(session_name="stop-current")
    pane = session.active_window.active_pane
    assert pane is not None
    assert pane.pane_id is not None

    monkeypatch.setenv("TMUX", "/tmp/tmux-test/default,123,0")
    monkeypatch.setenv("TMUX_PANE", pane.pane_id)

    command_stop(_stop_args(server, None))

    assert server.sessions.get(session_name="stop-current", default=None) is None


def test_command_stop_requires_name_outside_tmux(
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """command_stop() exits if no session name is given outside tmux."""
    monkeypatch.delenv("TMUX", raising=False)
    monkeypatch.delenv("TMUX_PANE", raising=False)

    with pytest.raises(SystemExit) as excinfo:
        command_stop(_stop_args(server, None))

    assert excinfo.value.code == 1
