"""Tests for CLI colors in freeze command."""

from __future__ import annotations

import pathlib

from tests.cli.conftest import (
    ANSI_BLUE,
    ANSI_CYAN,
    ANSI_GREEN,
    ANSI_RED,
    ANSI_RESET,
    ANSI_YELLOW,
)
from tmuxp._internal.private_path import PrivatePath
from tmuxp.cli._colors import Colors

# Freeze command color output tests


def test_freeze_error_uses_red(colors_always: Colors) -> None:
    """Verify error messages use error color (red)."""
    msg = "Session not found"
    result = colors_always.error(msg)
    assert ANSI_RED in result  # red foreground
    assert msg in result
    assert result.endswith(ANSI_RESET)  # reset at end


def test_freeze_success_message(colors_always: Colors) -> None:
    """Verify success messages use success color (green)."""
    result = colors_always.success("Saved to ")
    assert ANSI_GREEN in result  # green foreground
    assert "Saved to" in result


def test_freeze_file_path_uses_info(colors_always: Colors) -> None:
    """Verify file paths use info color (cyan)."""
    path = "/path/to/config.yaml"
    result = colors_always.info(path)
    assert ANSI_CYAN in result  # cyan foreground
    assert path in result


def test_freeze_warning_file_exists(colors_always: Colors) -> None:
    """Verify file exists warning uses warning color (yellow)."""
    msg = "/path/to/config.yaml exists."
    result = colors_always.warning(msg)
    assert ANSI_YELLOW in result  # yellow foreground
    assert msg in result


def test_freeze_muted_for_secondary_text(colors_always: Colors) -> None:
    """Verify secondary text uses muted color (blue)."""
    msg = "Freeze does its best to snapshot live tmux sessions."
    result = colors_always.muted(msg)
    assert ANSI_BLUE in result  # blue foreground
    assert msg in result


def test_freeze_colors_disabled_plain_text(colors_never: Colors) -> None:
    """Verify disabled colors return plain text."""
    assert colors_never.error("error") == "error"
    assert colors_never.success("success") == "success"
    assert colors_never.warning("warning") == "warning"
    assert colors_never.info("info") == "info"
    assert colors_never.muted("muted") == "muted"


def test_freeze_combined_output_format(colors_always: Colors) -> None:
    """Verify combined success + info format for 'Saved to <path>' message."""
    dest = "/home/user/.tmuxp/session.yaml"
    output = colors_always.success("Saved to ") + colors_always.info(dest) + "."
    # Should contain both green and cyan ANSI codes
    assert ANSI_GREEN in output  # green for "Saved to"
    assert ANSI_CYAN in output  # cyan for path
    assert "Saved to" in output
    assert dest in output
    assert output.endswith(".")


def test_freeze_warning_with_instructions(colors_always: Colors) -> None:
    """Verify warning + muted format for file exists message."""
    path = "/path/to/config.yaml"
    output = (
        colors_always.warning(f"{path} exists.")
        + " "
        + colors_always.muted("Pick a new filename.")
    )
    # Should contain both yellow and blue ANSI codes
    assert ANSI_YELLOW in output  # yellow for warning
    assert ANSI_BLUE in output  # blue for muted
    assert path in output
    assert "Pick a new filename." in output


def test_freeze_url_highlighted_in_help(colors_always: Colors) -> None:
    """Verify URLs use info color in help text."""
    url = "<http://tmuxp.git-pull.com/examples.html>"
    help_text = colors_always.muted("tmuxp has examples at ") + colors_always.info(url)
    assert ANSI_BLUE in help_text  # blue for muted text
    assert ANSI_CYAN in help_text  # cyan for URL
    assert url in help_text


# Privacy masking tests


def test_freeze_masks_home_in_saved_message(
    colors_always: Colors,
    mock_home: pathlib.Path,
) -> None:
    """Freeze should mask home directory in 'Saved to' message."""
    dest = mock_home / ".tmuxp/session.yaml"
    output = (
        colors_always.success("Saved to ")
        + colors_always.info(str(PrivatePath(dest)))
        + "."
    )

    assert "~/.tmuxp/session.yaml" in output
    assert "/home/testuser" not in output


def test_freeze_masks_home_in_exists_warning(
    colors_always: Colors,
    mock_home: pathlib.Path,
) -> None:
    """Freeze should mask home directory in 'exists' warning."""
    dest_prompt = mock_home / ".tmuxp/session.yaml"
    output = colors_always.warning(f"{PrivatePath(dest_prompt)} exists.")

    assert "~/.tmuxp/session.yaml exists." in output
    assert "/home/testuser" not in output


def test_freeze_masks_home_in_save_to_prompt(mock_home: pathlib.Path) -> None:
    """Freeze should mask home directory in 'Save to:' prompt."""
    save_to = mock_home / ".tmuxp/session.yaml"
    prompt_text = f"Save to: {PrivatePath(save_to)}"

    assert "~/.tmuxp/session.yaml" in prompt_text
    assert "/home/testuser" not in prompt_text


def test_freeze_masks_home_in_save_confirmation(mock_home: pathlib.Path) -> None:
    """Freeze should mask home directory in 'Save to ...?' confirmation."""
    dest = mock_home / ".tmuxp/session.yaml"
    prompt_text = f"Save to {PrivatePath(dest)}?"

    assert "~/.tmuxp/session.yaml" in prompt_text
    assert "/home/testuser" not in prompt_text
