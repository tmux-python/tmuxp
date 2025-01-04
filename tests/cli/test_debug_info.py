"""CLI tests for tmuxp debuginfo."""

from __future__ import annotations

import typing as t

from tmuxp import cli

if t.TYPE_CHECKING:
    import pathlib

    import pytest


def test_debug_info_cli(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Basic CLI test for tmuxp debug-info."""
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
