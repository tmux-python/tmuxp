"""CLI tests for tmuxp debug-info."""

from __future__ import annotations

import json
import typing as t

import pytest

from tmuxp import cli

if t.TYPE_CHECKING:
    import pathlib


class DebugInfoOutputFixture(t.NamedTuple):
    """Test fixture for debug-info output modes."""

    test_id: str
    args: list[str]
    expected_keys: list[str]
    is_json: bool


DEBUG_INFO_OUTPUT_FIXTURES: list[DebugInfoOutputFixture] = [
    DebugInfoOutputFixture(
        test_id="human_output_has_labels",
        args=["debug-info"],
        expected_keys=["environment", "python version", "tmux version"],
        is_json=False,
    ),
    DebugInfoOutputFixture(
        test_id="json_output_valid",
        args=["debug-info", "--json"],
        expected_keys=["environment", "python_version", "tmux_version"],
        is_json=True,
    ),
]


@pytest.mark.parametrize(
    DEBUG_INFO_OUTPUT_FIXTURES[0]._fields,
    [pytest.param(*f, id=f.test_id) for f in DEBUG_INFO_OUTPUT_FIXTURES],
)
def test_debug_info_output_modes(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    test_id: str,
    args: list[str],
    expected_keys: list[str],
    is_json: bool,
) -> None:
    """Test debug-info output modes (human and JSON)."""
    monkeypatch.setenv("SHELL", "/bin/bash")

    cli.cli(args)
    output = capsys.readouterr().out

    if is_json:
        data = json.loads(output)
        for key in expected_keys:
            assert key in data, f"Expected key '{key}' in JSON output"
    else:
        for key in expected_keys:
            assert key in output, f"Expected '{key}' in human output"


def test_debug_info_cli(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Basic CLI test for tmuxp debug-info (human output)."""
    monkeypatch.setenv("SHELL", "/bin/bash")

    cli.cli(["debug-info"])
    cli_output = capsys.readouterr().out
    assert "environment" in cli_output
    assert "python version" in cli_output
    assert "system PATH" in cli_output
    assert "tmux version" in cli_output
    assert "libtmux version" in cli_output
    assert "tmuxp version" in cli_output
    assert "tmux path" in cli_output
    assert "tmuxp path" in cli_output
    assert "shell" in cli_output
    assert "tmux session" in cli_output
    assert "tmux windows" in cli_output
    assert "tmux panes" in cli_output
    assert "tmux global options" in cli_output
    assert "tmux window options" in cli_output


def test_debug_info_json_output(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """JSON output is valid JSON with expected structure."""
    monkeypatch.setenv("SHELL", "/bin/bash")

    cli.cli(["debug-info", "--json"])
    output = capsys.readouterr().out

    data = json.loads(output)

    # Top-level keys
    assert "environment" in data
    assert "python_version" in data
    assert "system_path" in data
    assert "tmux_version" in data
    assert "libtmux_version" in data
    assert "tmuxp_version" in data
    assert "tmux_path" in data
    assert "tmuxp_path" in data
    assert "shell" in data
    assert "tmux" in data

    # Environment structure
    env = data["environment"]
    assert "dist" in env
    assert "arch" in env
    assert "uname" in env
    assert "version" in env
    assert isinstance(env["uname"], list)

    # Tmux structure
    tmux = data["tmux"]
    assert "sessions" in tmux
    assert "windows" in tmux
    assert "panes" in tmux
    assert "global_options" in tmux
    assert "window_options" in tmux
    assert isinstance(tmux["sessions"], list)


def test_debug_info_json_no_ansi(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """JSON output should not contain ANSI escape codes."""
    monkeypatch.setenv("SHELL", "/bin/bash")

    cli.cli(["debug-info", "--json"])
    output = capsys.readouterr().out

    # ANSI escape codes start with \x1b[ or \033[
    assert "\x1b[" not in output, "JSON output contains ANSI escape codes"
    assert "\033[" not in output, "JSON output contains ANSI escape codes"


def test_debug_info_json_paths_use_private_path(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """JSON output should mask home directory with ~."""
    import pathlib

    # Set SHELL to a path under home directory
    shell_path = pathlib.Path.home() / ".local" / "bin" / "zsh"
    monkeypatch.setenv("SHELL", str(shell_path))

    cli.cli(["debug-info", "--json"])
    output = capsys.readouterr().out
    data = json.loads(output)

    # The shell path should be masked with ~
    assert data["shell"] == "~/.local/bin/zsh", (
        f"Expected shell path to be masked with ~, got: {data['shell']}"
    )
