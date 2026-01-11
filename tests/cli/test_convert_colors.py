"""Tests for CLI colors in convert command."""

from __future__ import annotations

import pathlib

from tests.cli.conftest import ANSI_BOLD, ANSI_CYAN, ANSI_GREEN, ANSI_MAGENTA
from tmuxp._internal.private_path import PrivatePath
from tmuxp.cli._colors import Colors

# Convert command color output tests


def test_convert_success_message(colors_always: Colors) -> None:
    """Verify success messages use success color (green)."""
    result = colors_always.success("New workspace file saved to ")
    assert ANSI_GREEN in result  # green foreground
    assert "New workspace file saved to" in result


def test_convert_file_path_uses_info(colors_always: Colors) -> None:
    """Verify file paths use info color (cyan)."""
    path = "/path/to/config.yaml"
    result = colors_always.info(path)
    assert ANSI_CYAN in result  # cyan foreground
    assert path in result


def test_convert_format_type_highlighted(colors_always: Colors) -> None:
    """Verify format type uses highlight color (magenta + bold)."""
    for fmt in ["json", "yaml"]:
        result = colors_always.highlight(fmt)
        assert ANSI_MAGENTA in result  # magenta foreground
        assert ANSI_BOLD in result  # bold
        assert fmt in result


def test_convert_colors_disabled_plain_text(colors_never: Colors) -> None:
    """Verify disabled colors return plain text."""
    assert colors_never.success("success") == "success"
    assert colors_never.info("info") == "info"
    assert colors_never.highlight("highlight") == "highlight"


def test_convert_combined_success_format(colors_always: Colors) -> None:
    """Verify combined success + info format for save message."""
    newfile = "/home/user/.tmuxp/session.json"
    output = (
        colors_always.success("New workspace file saved to ")
        + colors_always.info(f"<{newfile}>")
        + "."
    )
    # Should contain both green and cyan ANSI codes
    assert ANSI_GREEN in output  # green for success text
    assert ANSI_CYAN in output  # cyan for path
    assert "New workspace file saved to" in output
    assert newfile in output
    assert output.endswith(".")


def test_convert_prompt_format_with_highlight(colors_always: Colors) -> None:
    """Verify prompt uses info for path and highlight for format."""
    workspace_file = "/path/to/config.yaml"
    to_filetype = "json"
    prompt = (
        f"Convert {colors_always.info(workspace_file)} "
        f"to {colors_always.highlight(to_filetype)}?"
    )
    assert ANSI_CYAN in prompt  # cyan for file path
    assert ANSI_MAGENTA in prompt  # magenta for format type
    assert workspace_file in prompt
    assert to_filetype in prompt


def test_convert_save_prompt_format(colors_always: Colors) -> None:
    """Verify save prompt uses info color for new file path."""
    newfile = "/path/to/config.json"
    prompt = f"Save workspace to {colors_always.info(newfile)}?"
    assert ANSI_CYAN in prompt  # cyan for file path
    assert newfile in prompt
    assert "Save workspace to" in prompt


# Privacy masking tests


def test_convert_masks_home_in_convert_prompt(
    colors_always: Colors,
    mock_home: pathlib.Path,
) -> None:
    """Convert should mask home directory in convert prompt."""
    workspace_file = mock_home / ".tmuxp/session.yaml"
    prompt = f"Convert {colors_always.info(str(PrivatePath(workspace_file)))} to json?"

    assert "~/.tmuxp/session.yaml" in prompt
    assert "/home/testuser" not in prompt


def test_convert_masks_home_in_save_prompt(
    colors_always: Colors,
    mock_home: pathlib.Path,
) -> None:
    """Convert should mask home directory in save prompt."""
    newfile = mock_home / ".tmuxp/session.json"
    prompt = f"Save workspace to {colors_always.info(str(PrivatePath(newfile)))}?"

    assert "~/.tmuxp/session.json" in prompt
    assert "/home/testuser" not in prompt


def test_convert_masks_home_in_saved_message(
    colors_always: Colors,
    mock_home: pathlib.Path,
) -> None:
    """Convert should mask home directory in saved message."""
    newfile = mock_home / ".tmuxp/session.json"
    output = (
        colors_always.success("New workspace file saved to ")
        + colors_always.info(str(PrivatePath(newfile)))
        + "."
    )

    assert "~/.tmuxp/session.json" in output
    assert "/home/testuser" not in output
