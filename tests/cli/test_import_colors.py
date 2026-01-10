"""Tests for CLI colors in import command."""

from __future__ import annotations

import pathlib

from tests.cli.conftest import (
    ANSI_BLUE,
    ANSI_CYAN,
    ANSI_GREEN,
    ANSI_RED,
    ANSI_RESET,
)
from tmuxp._internal.private_path import PrivatePath
from tmuxp.cli._colors import Colors

# Import command color output tests


def test_import_error_unknown_format(colors_always: Colors) -> None:
    """Verify unknown format error uses error color (red)."""
    msg = "Unknown config format."
    result = colors_always.error(msg)
    assert ANSI_RED in result  # red foreground
    assert msg in result
    assert result.endswith(ANSI_RESET)  # reset at end


def test_import_success_message(colors_always: Colors) -> None:
    """Verify success messages use success color (green)."""
    result = colors_always.success("Saved to ")
    assert ANSI_GREEN in result  # green foreground
    assert "Saved to" in result


def test_import_file_path_uses_info(colors_always: Colors) -> None:
    """Verify file paths use info color (cyan)."""
    path = "/path/to/config.yaml"
    result = colors_always.info(path)
    assert ANSI_CYAN in result  # cyan foreground
    assert path in result


def test_import_muted_for_banner(colors_always: Colors) -> None:
    """Verify banner text uses muted color (blue)."""
    msg = "Configuration import does its best to convert files."
    result = colors_always.muted(msg)
    assert ANSI_BLUE in result  # blue foreground
    assert msg in result


def test_import_muted_for_separator(colors_always: Colors) -> None:
    """Verify separator uses muted color (blue)."""
    separator = "---------------------------------------------------------------"
    result = colors_always.muted(separator)
    assert ANSI_BLUE in result  # blue foreground
    assert separator in result


def test_import_colors_disabled_plain_text(colors_never: Colors) -> None:
    """Verify disabled colors return plain text."""
    assert colors_never.error("error") == "error"
    assert colors_never.success("success") == "success"
    assert colors_never.muted("muted") == "muted"
    assert colors_never.info("info") == "info"


def test_import_combined_success_format(colors_always: Colors) -> None:
    """Verify combined success + info format for 'Saved to <path>' message."""
    dest = "/home/user/.tmuxp/session.yaml"
    output = colors_always.success("Saved to ") + colors_always.info(dest) + "."
    # Should contain both green and cyan ANSI codes
    assert ANSI_GREEN in output  # green for "Saved to"
    assert ANSI_CYAN in output  # cyan for path
    assert "Saved to" in output
    assert dest in output
    assert output.endswith(".")


def test_import_help_text_with_urls(colors_always: Colors) -> None:
    """Verify help text uses muted for text and info for URLs."""
    url = "<http://tmuxp.git-pull.com/examples.html>"
    help_text = colors_always.muted(
        "tmuxp has examples in JSON and YAML format at "
    ) + colors_always.info(url)
    assert ANSI_BLUE in help_text  # blue for muted text
    assert ANSI_CYAN in help_text  # cyan for URL
    assert url in help_text


def test_import_banner_with_separator(colors_always: Colors) -> None:
    """Verify banner format with separator and instruction text."""
    config_content = "session_name: test\n"
    separator = "---------------------------------------------------------------"
    output = (
        config_content
        + colors_always.muted(separator)
        + "\n"
        + colors_always.muted("Configuration import does its best to convert files.")
        + "\n"
    )
    # Should contain blue ANSI code for muted sections
    assert ANSI_BLUE in output
    assert separator in output
    assert "Configuration import" in output
    assert config_content in output


# Privacy masking tests


def test_import_masks_home_in_save_prompt(mock_home: pathlib.Path) -> None:
    """Import should mask home directory in save prompt."""
    cwd = mock_home / "projects"
    prompt = f"Save to [{PrivatePath(cwd)}]"

    assert "[~/projects]" in prompt
    assert "/home/testuser" not in prompt


def test_import_masks_home_in_confirm_prompt(mock_home: pathlib.Path) -> None:
    """Import should mask home directory in confirmation prompt."""
    dest_path = mock_home / ".tmuxp/imported.yaml"
    prompt = f"Save to {PrivatePath(dest_path)}?"

    assert "~/.tmuxp/imported.yaml" in prompt
    assert "/home/testuser" not in prompt


def test_import_masks_home_in_saved_message(
    colors_always: Colors,
    mock_home: pathlib.Path,
) -> None:
    """Import should mask home directory in 'Saved to' message."""
    dest = mock_home / ".tmuxp/imported.yaml"
    output = (
        colors_always.success("Saved to ")
        + colors_always.info(str(PrivatePath(dest)))
        + "."
    )

    assert "~/.tmuxp/imported.yaml" in output
    assert "/home/testuser" not in output
