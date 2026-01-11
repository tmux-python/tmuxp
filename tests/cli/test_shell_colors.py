"""Tests for CLI colors in shell command."""

from __future__ import annotations

from tests.cli.conftest import ANSI_BLUE, ANSI_BOLD, ANSI_CYAN, ANSI_MAGENTA
from tmuxp.cli._colors import Colors

# Shell command color output tests


def test_shell_launch_message_format(colors_always: Colors) -> None:
    """Verify launch message format with shell type and session."""
    shell_name = "ipython"
    session_name = "my-session"
    output = (
        colors_always.muted("Launching ")
        + colors_always.highlight(shell_name, bold=False)
        + colors_always.muted(" shell for session ")
        + colors_always.info(session_name)
        + colors_always.muted("...")
    )
    # Should contain blue, magenta, and cyan ANSI codes
    assert ANSI_BLUE in output  # blue for muted
    assert ANSI_MAGENTA in output  # magenta for highlight
    assert ANSI_CYAN in output  # cyan for session name
    assert shell_name in output
    assert session_name in output


def test_shell_pdb_launch_message(colors_always: Colors) -> None:
    """Verify pdb launch message format."""
    output = (
        colors_always.muted("Launching ")
        + colors_always.highlight("pdb", bold=False)
        + colors_always.muted(" shell...")
    )
    assert ANSI_BLUE in output  # blue for muted
    assert ANSI_MAGENTA in output  # magenta for pdb
    assert "pdb" in output


def test_shell_highlight_not_bold(colors_always: Colors) -> None:
    """Verify shell name uses highlight without bold for subtlety."""
    result = colors_always.highlight("best", bold=False)
    assert ANSI_MAGENTA in result  # magenta foreground
    assert ANSI_BOLD not in result  # no bold - subtle emphasis
    assert "best" in result


def test_shell_session_name_uses_info(colors_always: Colors) -> None:
    """Verify session name uses info color (cyan)."""
    session_name = "dev-session"
    result = colors_always.info(session_name)
    assert ANSI_CYAN in result  # cyan foreground
    assert session_name in result


def test_shell_muted_for_static_text(colors_always: Colors) -> None:
    """Verify static text uses muted color (blue)."""
    result = colors_always.muted("Launching ")
    assert ANSI_BLUE in result  # blue foreground
    assert "Launching" in result


def test_shell_colors_disabled_plain_text(colors_never: Colors) -> None:
    """Verify disabled colors return plain text."""
    shell_name = "ipython"
    session_name = "my-session"
    output = (
        colors_never.muted("Launching ")
        + colors_never.highlight(shell_name, bold=False)
        + colors_never.muted(" shell for session ")
        + colors_never.info(session_name)
        + colors_never.muted("...")
    )
    # Should be plain text without ANSI codes
    assert "\033[" not in output
    assert output == f"Launching {shell_name} shell for session {session_name}..."


def test_shell_various_shell_names(colors_always: Colors) -> None:
    """Verify all shell types can be highlighted."""
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
        result = colors_always.highlight(shell_name, bold=False)
        assert ANSI_MAGENTA in result
        assert shell_name in result
