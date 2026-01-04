"""Tests for CLI colors in shell command."""

from __future__ import annotations

import pytest

from tmuxp.cli._colors import ColorMode, Colors

# Shell command color output tests


def test_shell_launch_message_format(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify launch message format with shell type and session."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    shell_name = "ipython"
    session_name = "my-session"
    output = (
        colors.muted("Launching ")
        + colors.highlight(shell_name, bold=False)
        + colors.muted(" shell for session ")
        + colors.info(session_name)
        + colors.muted("...")
    )
    # Should contain blue, magenta, and cyan ANSI codes
    assert "\033[34m" in output  # blue for muted
    assert "\033[35m" in output  # magenta for highlight
    assert "\033[36m" in output  # cyan for session name
    assert shell_name in output
    assert session_name in output


def test_shell_pdb_launch_message(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify pdb launch message format."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    output = (
        colors.muted("Launching ")
        + colors.highlight("pdb", bold=False)
        + colors.muted(" shell...")
    )
    assert "\033[34m" in output  # blue for muted
    assert "\033[35m" in output  # magenta for pdb
    assert "pdb" in output


def test_shell_highlight_not_bold(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify shell name uses highlight without bold for subtlety."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    result = colors.highlight("best", bold=False)
    assert "\033[35m" in result  # magenta foreground
    assert "\033[1m" not in result  # no bold - subtle emphasis
    assert "best" in result


def test_shell_session_name_uses_info(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify session name uses info color (cyan)."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    session_name = "dev-session"
    result = colors.info(session_name)
    assert "\033[36m" in result  # cyan foreground
    assert session_name in result


def test_shell_muted_for_static_text(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify static text uses muted color (blue)."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    result = colors.muted("Launching ")
    assert "\033[34m" in result  # blue foreground
    assert "Launching" in result


def test_shell_colors_disabled_plain_text() -> None:
    """Verify disabled colors return plain text."""
    colors = Colors(ColorMode.NEVER)

    shell_name = "ipython"
    session_name = "my-session"
    output = (
        colors.muted("Launching ")
        + colors.highlight(shell_name, bold=False)
        + colors.muted(" shell for session ")
        + colors.info(session_name)
        + colors.muted("...")
    )
    # Should be plain text without ANSI codes
    assert "\033[" not in output
    assert output == f"Launching {shell_name} shell for session {session_name}..."


def test_shell_various_shell_names(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify all shell types can be highlighted."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    shell_types = [
        "best",
        "pdb",
        "code",
        "ptipython",
        "ptpython",
        "ipython",
        "bpython",
    ]
    for shell_name in shell_types:
        result = colors.highlight(shell_name, bold=False)
        assert "\033[35m" in result
        assert shell_name in result
