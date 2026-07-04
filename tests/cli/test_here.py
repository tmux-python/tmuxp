"""Tests for ``tmuxp load --here``."""

from __future__ import annotations

import pathlib

import pytest

from tmuxp import exc
from tmuxp.cli.load import load_workspace


def test_load_with_here_outside_tmux_errors(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """--here outside an existing tmux session raises TmuxpException."""
    workspace = tmp_path / "ws.yaml"
    workspace.write_text(
        "session_name: t4-outside\n"
        "windows:\n- window_name: w1\n  panes:\n  - shell_command:\n    - echo hi\n",
    )
    monkeypatch.delenv("TMUX", raising=False)
    with pytest.raises(exc.TmuxpException, match="--here requires being inside"):
        load_workspace(workspace, here=True, detached=True)


def test_load_with_here_and_append_errors(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """--here + --append are mutually exclusive."""
    workspace = tmp_path / "ws.yaml"
    workspace.write_text(
        "session_name: t4-mutex\n"
        "windows:\n- window_name: w1\n  panes:\n  - shell_command:\n    - echo hi\n",
    )
    # Set TMUX so we get past the second precondition; the mutex check fires
    # first.
    monkeypatch.setenv("TMUX", "/tmp/fake-tmux-socket,0,0")
    with pytest.raises(exc.TmuxpException, match="mutually exclusive"):
        load_workspace(workspace, here=True, append=True, detached=True)
