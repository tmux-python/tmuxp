"""Tests for tmuxp's utility functions."""

from __future__ import annotations

import logging
import os
import pathlib
import sys
import typing as t

import pytest

from tmuxp import exc
from tmuxp.exc import BeforeLoadScriptError, BeforeLoadScriptNotExists
from tmuxp.util import (
    get_pane,
    get_session,
    oh_my_zsh_auto_title,
    run_before_script,
    run_hook_commands,
)

from .constants import FIXTURE_PATH

if t.TYPE_CHECKING:
    import pathlib

    from libtmux.server import Server


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


@pytest.fixture
def temp_script(tmp_path: pathlib.Path) -> pathlib.Path:
    """Fixture of an example script that prints "Hello, world!"."""
    script = tmp_path / "test_script.sh"
    script.write_text(
        """#!/bin/sh
echo "Hello, World!"
exit 0
""",
    )
    script.chmod(0o755)
    return script


class TTYTestFixture(t.NamedTuple):
    """Test fixture for isatty behavior verification."""

    test_id: str
    isatty_value: bool
    expected_output: str


TTY_TEST_FIXTURES: list[TTYTestFixture] = [
    TTYTestFixture(
        test_id="tty_enabled_shows_output",
        isatty_value=True,
        expected_output="Hello, World!",
    ),
    TTYTestFixture(
        test_id="tty_disabled_suppresses_output",
        isatty_value=False,
        expected_output="",
    ),
]


@pytest.mark.parametrize(
    list(TTYTestFixture._fields),
    TTY_TEST_FIXTURES,
    ids=[test.test_id for test in TTY_TEST_FIXTURES],
)
def test_run_before_script_isatty(
    temp_script: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    test_id: str,
    isatty_value: bool,
    expected_output: str,
) -> None:
    """Verify behavior of ``isatty()``, which we mock in `run_before_script()`."""
    # Mock sys.stdout.isatty() to return the desired value.
    monkeypatch.setattr(sys.stdout, "isatty", lambda: isatty_value)

    # Run the script.
    returncode = run_before_script(temp_script)

    # Assert that the script ran successfully.
    assert returncode == 0

    out, _err = capsys.readouterr()

    # In TTY mode, we expect the output; in non-TTY mode, we expect it to be suppressed.
    assert expected_output in out


def test_return_stdout_if_ok(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """run_before_script() returns stdout if script succeeds."""
    # Simulate sys.stdout.isatty() + sys.stderr.isatty()
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr(sys.stderr, "isatty", lambda: True)

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
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """get_session() should return first session if no active session."""
    # Clear outer tmux environment to ensure no active pane interferes
    monkeypatch.delenv("TMUX_PANE", raising=False)
    monkeypatch.delenv("TMUX", raising=False)

    first_session = server.new_session(session_name="myfirstsession")
    server.new_session(session_name="mysecondsession")

    assert get_session(server) == first_session


def test_get_pane_logs_debug_on_failure(
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """get_pane() logs DEBUG with tmux_pane extra when pane lookup fails."""
    session = server.new_session(session_name="test_pane_log")
    window = session.active_window

    # Make active_pane raise Exception to trigger the logging path
    monkeypatch.setattr(
        type(window),
        "active_pane",
        property(lambda self: (_ for _ in ()).throw(Exception("mock pane error"))),
    )

    with (
        caplog.at_level(logging.DEBUG, logger="tmuxp.util"),
        pytest.raises(exc.PaneNotFound),
    ):
        get_pane(window, current_pane=None)

    debug_records = [
        r
        for r in caplog.records
        if hasattr(r, "tmux_pane") and r.levelno == logging.DEBUG
    ]
    assert len(debug_records) >= 1
    assert debug_records[0].tmux_pane == ""


def test_oh_my_zsh_auto_title_logs_warning(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    tmp_path: t.Any,
) -> None:
    """oh_my_zsh_auto_title() logs WARNING when DISABLE_AUTO_TITLE not set."""
    monkeypatch.setenv("SHELL", "/bin/zsh")
    monkeypatch.delenv("DISABLE_AUTO_TITLE", raising=False)

    # Create fake ~/.oh-my-zsh directory
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    oh_my_zsh_dir = fake_home / ".oh-my-zsh"
    oh_my_zsh_dir.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    # Patch os.path.exists to return True for ~/.oh-my-zsh
    original_exists = os.path.exists

    def patched_exists(path: str) -> bool:
        if path == str(pathlib.Path("~/.oh-my-zsh").expanduser()):
            return True
        return original_exists(path)

    monkeypatch.setattr(os.path, "exists", patched_exists)

    with caplog.at_level(logging.WARNING, logger="tmuxp.util"):
        oh_my_zsh_auto_title()

    warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warning_records) >= 1
    assert "DISABLE_AUTO_TITLE" in warning_records[0].message


class HookCommandFixture(t.NamedTuple):
    """Test fixture for run_hook_commands."""

    test_id: str
    commands: str | list[str]
    expect_runs: bool


HOOK_COMMAND_FIXTURES: list[HookCommandFixture] = [
    HookCommandFixture(
        test_id="string-cmd",
        commands="echo hello",
        expect_runs=True,
    ),
    HookCommandFixture(
        test_id="list-cmd",
        commands=["echo a", "echo b"],
        expect_runs=True,
    ),
    HookCommandFixture(
        test_id="empty-string",
        commands="",
        expect_runs=False,
    ),
]


@pytest.mark.parametrize(
    list(HookCommandFixture._fields),
    HOOK_COMMAND_FIXTURES,
    ids=[f.test_id for f in HOOK_COMMAND_FIXTURES],
)
def test_run_hook_commands(
    tmp_path: pathlib.Path,
    test_id: str,
    commands: str | list[str],
    expect_runs: bool,
) -> None:
    """run_hook_commands() executes shell commands without raising."""
    if expect_runs:
        marker = tmp_path / "hook_ran"
        if isinstance(commands, str):
            commands = f"touch {marker}"
        else:
            commands = [f"touch {marker}"]
        run_hook_commands(commands)
        assert marker.exists()
    else:
        # Should not raise
        run_hook_commands(commands)


def test_run_hook_commands_failure_warns(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """run_hook_commands() logs WARNING on non-zero exit, does not raise."""
    with caplog.at_level(logging.WARNING, logger="tmuxp.util"):
        run_hook_commands("exit 1")

    warning_records = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING and hasattr(r, "tmux_exit_code")
    ]
    assert len(warning_records) >= 1
    assert warning_records[0].tmux_exit_code == 1


def test_run_hook_commands_cwd(
    tmp_path: pathlib.Path,
) -> None:
    """run_hook_commands() respects cwd parameter."""
    run_hook_commands("touch marker_file", cwd=tmp_path)
    assert (tmp_path / "marker_file").exists()
