"""Tests for CLI colors in import command."""

from __future__ import annotations

import pathlib

import pytest

from tmuxp._internal.private_path import PrivatePath
from tmuxp.cli._colors import ColorMode, Colors

# Import command color output tests


def test_import_error_unknown_format(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify unknown format error uses error color (red)."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    msg = "Unknown config format."
    result = colors.error(msg)
    assert "\033[31m" in result  # red foreground
    assert msg in result
    assert result.endswith("\033[0m")  # reset at end


def test_import_success_message(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify success messages use success color (green)."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    result = colors.success("Saved to ")
    assert "\033[32m" in result  # green foreground
    assert "Saved to" in result


def test_import_file_path_uses_info(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify file paths use info color (cyan)."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    path = "/path/to/config.yaml"
    result = colors.info(path)
    assert "\033[36m" in result  # cyan foreground
    assert path in result


def test_import_muted_for_banner(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify banner text uses muted color (blue)."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    msg = "Configuration import does its best to convert files."
    result = colors.muted(msg)
    assert "\033[34m" in result  # blue foreground
    assert msg in result


def test_import_muted_for_separator(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify separator uses muted color (blue)."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    separator = "---------------------------------------------------------------"
    result = colors.muted(separator)
    assert "\033[34m" in result  # blue foreground
    assert separator in result


def test_import_colors_disabled_plain_text() -> None:
    """Verify disabled colors return plain text."""
    colors = Colors(ColorMode.NEVER)

    assert colors.error("error") == "error"
    assert colors.success("success") == "success"
    assert colors.muted("muted") == "muted"
    assert colors.info("info") == "info"


def test_import_combined_success_format(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify combined success + info format for 'Saved to <path>' message."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    dest = "/home/user/.tmuxp/session.yaml"
    output = colors.success("Saved to ") + colors.info(dest) + "."
    # Should contain both green and cyan ANSI codes
    assert "\033[32m" in output  # green for "Saved to"
    assert "\033[36m" in output  # cyan for path
    assert "Saved to" in output
    assert dest in output
    assert output.endswith(".")


def test_import_help_text_with_urls(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify help text uses muted for text and info for URLs."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    url = "<http://tmuxp.git-pull.com/examples.html>"
    help_text = colors.muted(
        "tmuxp has examples in JSON and YAML format at "
    ) + colors.info(url)
    assert "\033[34m" in help_text  # blue for muted text
    assert "\033[36m" in help_text  # cyan for URL
    assert url in help_text


def test_import_banner_with_separator(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify banner format with separator and instruction text."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    config_content = "session_name: test\n"
    separator = "---------------------------------------------------------------"
    output = (
        config_content
        + colors.muted(separator)
        + "\n"
        + colors.muted("Configuration import does its best to convert files.")
        + "\n"
    )
    # Should contain blue ANSI code for muted sections
    assert "\033[34m" in output
    assert separator in output
    assert "Configuration import" in output
    assert config_content in output


# Privacy masking tests


def test_import_masks_home_in_save_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    """Import should mask home directory in save prompt."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: pathlib.Path("/home/testuser"))

    cwd = "/home/testuser/projects"
    prompt = f"Save to [{PrivatePath(cwd)}]"

    assert "[~/projects]" in prompt
    assert "/home/testuser" not in prompt


def test_import_masks_home_in_confirm_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    """Import should mask home directory in confirmation prompt."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: pathlib.Path("/home/testuser"))

    dest_path = "/home/testuser/.tmuxp/imported.yaml"
    prompt = f"Save to {PrivatePath(dest_path)}?"

    assert "~/.tmuxp/imported.yaml" in prompt
    assert "/home/testuser" not in prompt


def test_import_masks_home_in_saved_message(monkeypatch: pytest.MonkeyPatch) -> None:
    """Import should mask home directory in 'Saved to' message."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: pathlib.Path("/home/testuser"))
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    dest = "/home/testuser/.tmuxp/imported.yaml"
    output = colors.success("Saved to ") + colors.info(str(PrivatePath(dest))) + "."

    assert "~/.tmuxp/imported.yaml" in output
    assert "/home/testuser" not in output
