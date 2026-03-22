"""Test tmuxp stop command."""

from __future__ import annotations

import pathlib
import typing as t

import pytest

from tmuxp import cli
from tmuxp.cli.load import load_workspace

if t.TYPE_CHECKING:
    from libtmux.server import Server


class StopTestFixture(t.NamedTuple):
    """Test fixture for tmuxp stop command tests."""

    test_id: str
    cli_args: list[str]
    session_name: str


STOP_TEST_FIXTURES: list[StopTestFixture] = [
    StopTestFixture(
        test_id="stop-named-session",
        cli_args=["stop", "killme"],
        session_name="killme",
    ),
]


@pytest.mark.parametrize(
    list(StopTestFixture._fields),
    STOP_TEST_FIXTURES,
    ids=[test.test_id for test in STOP_TEST_FIXTURES],
)
def test_stop(
    server: Server,
    test_id: str,
    cli_args: list[str],
    session_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test stopping a tmux session by name."""
    monkeypatch.delenv("TMUX", raising=False)

    server.new_session(session_name=session_name)
    assert server.has_session(session_name)

    assert server.socket_name is not None
    cli_args = [*cli_args, "-L", server.socket_name]

    cli.cli(cli_args)

    assert not server.has_session(session_name)


def test_stop_nonexistent_session(
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test stopping a session that doesn't exist shows error."""
    monkeypatch.delenv("TMUX", raising=False)

    assert server.socket_name is not None

    cli.cli(["stop", "nonexistent", "-L", server.socket_name])

    captured = capsys.readouterr()
    assert "Session not found" in captured.out


def test_stop_runs_on_project_stop_hook(
    tmp_path: pathlib.Path,
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tmuxp stop runs on_project_stop hook from session environment."""
    monkeypatch.delenv("TMUX", raising=False)

    marker = tmp_path / "stop_hook_ran"
    workspace_file = tmp_path / "hook_stop.yaml"
    workspace_file.write_text(
        f"""\
session_name: hook-stop-test
on_project_stop: "touch {marker}"
windows:
- window_name: main
  panes:
  - echo hello
""",
        encoding="utf-8",
    )

    session = load_workspace(
        workspace_file,
        socket_name=server.socket_name,
        detached=True,
    )
    assert session is not None

    # Verify env var was stored
    stop_cmd = session.getenv("TMUXP_ON_PROJECT_STOP")
    assert stop_cmd is not None

    # Stop the session via CLI
    assert server.socket_name is not None
    cli.cli(["stop", "hook-stop-test", "-L", server.socket_name])

    assert marker.exists()
    assert not server.has_session("hook-stop-test")


def test_stop_no_args_uses_fallback(
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tmuxp stop with no session name falls back to first session."""
    monkeypatch.delenv("TMUX", raising=False)

    server.new_session(session_name="fallback-target")
    assert server.has_session("fallback-target")

    assert server.socket_name is not None
    cli.cli(["stop", "-L", server.socket_name])

    assert not server.has_session("fallback-target")


def test_stop_without_hook(
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tmuxp stop works normally when no on_project_stop hook is set."""
    monkeypatch.delenv("TMUX", raising=False)

    server.new_session(session_name="no-hook-session")
    assert server.has_session("no-hook-session")

    assert server.socket_name is not None
    cli.cli(["stop", "no-hook-session", "-L", server.socket_name])

    assert not server.has_session("no-hook-session")
