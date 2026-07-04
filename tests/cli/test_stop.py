"""Tests for ``tmuxp stop``."""

from __future__ import annotations

import pathlib
import typing as t

from tmuxp.cli.stop import CLIStopNamespace, command_stop

if t.TYPE_CHECKING:
    from libtmux.server import Server
    from libtmux.session import Session


def test_command_stop_kills_running_session(
    session: Session,
    tmp_path: pathlib.Path,
) -> None:
    """`tmuxp stop` removes a running session that matches the config."""
    server = session.server
    name = session.name or ""
    assert name
    workspace = tmp_path / "test_stop.yaml"
    workspace.write_text(
        f"session_name: {name}\n"
        "windows:\n- window_name: w1\n  panes:\n  - shell_command:\n    - echo hi\n",
    )
    args = CLIStopNamespace(
        workspace_file=str(workspace),
        socket_name=server.socket_name,
        socket_path=server.socket_path,
        color=None,
    )
    assert server.has_session(name)
    command_stop(args)
    assert not server.has_session(name)


def test_command_stop_runs_on_project_stop_before_kill(
    session: Session,
    tmp_path: pathlib.Path,
) -> None:
    """on_project_stop hook fires before the session is killed."""
    server = session.server
    name = session.name or ""
    assert name
    marker = tmp_path / "marker.log"
    hook = tmp_path / "stop_hook.sh"
    hook.write_text(f"#!/bin/sh\necho fired > {marker}\n")
    hook.chmod(0o755)

    workspace = tmp_path / "test_stop_hook.yaml"
    workspace.write_text(
        f"session_name: {name}\n"
        f"on_project_stop: {hook}\n"
        "windows:\n- window_name: w1\n  panes:\n  - shell_command:\n    - echo hi\n",
    )
    args = CLIStopNamespace(
        workspace_file=str(workspace),
        socket_name=server.socket_name,
        socket_path=server.socket_path,
        color=None,
    )
    command_stop(args)
    assert marker.exists()
    assert marker.read_text().strip() == "fired"
    assert not server.has_session(name)


def test_command_stop_no_session_is_noop(
    server: Server,
    tmp_path: pathlib.Path,
) -> None:
    """Stopping a non-existent session is a quiet no-op."""
    workspace = tmp_path / "test_stop_missing.yaml"
    workspace.write_text(
        "session_name: definitely-not-running-aaa-bbb\n"
        "windows:\n- window_name: w1\n  panes:\n  - shell_command:\n    - echo hi\n",
    )
    args = CLIStopNamespace(
        workspace_file=str(workspace),
        socket_name=server.socket_name,
        socket_path=server.socket_path,
        color=None,
    )
    command_stop(args)  # must not raise
