"""Tests for CLI colors in edit command."""

from __future__ import annotations

import pathlib

from tests.cli.conftest import ANSI_BLUE, ANSI_BOLD, ANSI_CYAN, ANSI_MAGENTA
from tmuxp._internal.private_path import PrivatePath
from tmuxp.cli._colors import Colors

# Edit command color output tests


def test_edit_opening_message_format(colors_always: Colors) -> None:
    """Verify opening message format with file path and editor."""
    workspace_file = "/home/user/.tmuxp/dev.yaml"
    editor = "vim"
    output = (
        colors_always.muted("Opening ")
        + colors_always.info(workspace_file)
        + colors_always.muted(" in ")
        + colors_always.highlight(editor, bold=False)
        + colors_always.muted("...")
    )
    # Should contain blue, cyan, and magenta ANSI codes
    assert ANSI_BLUE in output  # blue for muted
    assert ANSI_CYAN in output  # cyan for file path
    assert ANSI_MAGENTA in output  # magenta for editor
    assert workspace_file in output
    assert editor in output


def test_edit_file_path_uses_info(colors_always: Colors) -> None:
    """Verify file paths use info color (cyan)."""
    path = "/path/to/workspace.yaml"
    result = colors_always.info(path)
    assert ANSI_CYAN in result  # cyan foreground
    assert path in result


def test_edit_editor_highlighted(colors_always: Colors) -> None:
    """Verify editor name uses highlight color without bold."""
    for editor in ["vim", "nano", "code", "emacs", "nvim"]:
        result = colors_always.highlight(editor, bold=False)
        assert ANSI_MAGENTA in result  # magenta foreground
        assert ANSI_BOLD not in result  # no bold - subtle
        assert editor in result


def test_edit_muted_for_static_text(colors_always: Colors) -> None:
    """Verify static text uses muted color (blue)."""
    result = colors_always.muted("Opening ")
    assert ANSI_BLUE in result  # blue foreground
    assert "Opening" in result


def test_edit_colors_disabled_plain_text(colors_never: Colors) -> None:
    """Verify disabled colors return plain text."""
    workspace_file = "/home/user/.tmuxp/dev.yaml"
    editor = "vim"
    output = (
        colors_never.muted("Opening ")
        + colors_never.info(workspace_file)
        + colors_never.muted(" in ")
        + colors_never.highlight(editor, bold=False)
        + colors_never.muted("...")
    )
    # Should be plain text without ANSI codes
    assert "\033[" not in output
    assert output == f"Opening {workspace_file} in {editor}..."


def test_edit_various_editors(colors_always: Colors) -> None:
    """Verify common editors can be highlighted."""
    editors = ["vim", "nvim", "nano", "code", "emacs", "hx", "micro"]
    for editor in editors:
        result = colors_always.highlight(editor, bold=False)
        assert ANSI_MAGENTA in result
        assert editor in result


# Privacy masking tests


def test_edit_masks_home_in_opening_message(
    colors_always: Colors,
    mock_home: pathlib.Path,
) -> None:
    """Edit should mask home directory in 'Opening' message."""
    workspace_file = mock_home / ".tmuxp/dev.yaml"
    editor = "vim"
    output = (
        colors_always.muted("Opening ")
        + colors_always.info(str(PrivatePath(workspace_file)))
        + colors_always.muted(" in ")
        + colors_always.highlight(editor, bold=False)
        + colors_always.muted("...")
    )

    assert "~/.tmuxp/dev.yaml" in output
    assert "/home/testuser" not in output
