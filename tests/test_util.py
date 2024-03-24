"""Tests for tmuxp's utility functions."""

import pytest
from libtmux.server import Server

from tmuxp import exc
from tmuxp.exc import BeforeLoadScriptError, BeforeLoadScriptNotExists
from tmuxp.util import get_session, run_before_script

from .constants import FIXTURE_PATH


def test_run_before_script_raise_BeforeLoadScriptNotExists_if_not_exists() -> None:
    """run_before_script() raises BeforeLoadScriptNotExists if script not found."""
    script_file = FIXTURE_PATH / "script_noexists.sh"

    with pytest.raises(BeforeLoadScriptNotExists):
        run_before_script(script_file)

    with pytest.raises(OSError):
        run_before_script(script_file)


def test_run_before_script_raise_BeforeLoadScriptError_if_retcode() -> None:
    """run_before_script() raises BeforeLoadScriptNotExists if script fails."""
    script_file = FIXTURE_PATH / "script_failed.sh"

    with pytest.raises(BeforeLoadScriptError):
        run_before_script(script_file)


def test_return_stdout_if_ok(capsys: pytest.CaptureFixture[str]) -> None:
    """run_before_script() returns stdout if script succeeds."""
    script_file = FIXTURE_PATH / "script_complete.sh"

    run_before_script(script_file)
    out, _err = capsys.readouterr()
    assert "hello" in out


def test_beforeload_returncode() -> None:
    """run_before_script() returns returncode if script fails."""
    script_file = FIXTURE_PATH / "script_failed.sh"

    with pytest.raises(exc.BeforeLoadScriptError) as excinfo:
        run_before_script(script_file)
        assert excinfo.match(r"113")


def test_beforeload_returns_stderr_messages() -> None:
    """run_before_script() returns stderr messages if script fails."""
    script_file = FIXTURE_PATH / "script_failed.sh"

    with pytest.raises(exc.BeforeLoadScriptError) as excinfo:
        run_before_script(script_file)
        assert excinfo.match(r"failed with returncode")


def test_get_session_should_default_to_local_attached_session(
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """get_session() should launch current terminal's tmux session, if inside one."""
    server.new_session(session_name="myfirstsession")
    second_session = server.new_session(session_name="mysecondsession")

    # Assign an active pane to the session
    first_pane_on_second_session_id = second_session.windows[0].panes[0].pane_id
    assert first_pane_on_second_session_id is not None
    monkeypatch.setenv("TMUX_PANE", first_pane_on_second_session_id)

    assert get_session(server) == second_session


def test_get_session_should_return_first_session_if_no_active_session(
    server: Server,
) -> None:
    """get_session() should return first session if no active session."""
    first_session = server.new_session(session_name="myfirstsession")
    server.new_session(session_name="mysecondsession")

    assert get_session(server) == first_session
