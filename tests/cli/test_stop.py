"""Test tmuxp stop command."""

from __future__ import annotations

import typing as t

import pytest

from tmuxp import cli

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
