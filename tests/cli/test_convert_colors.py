"""Tests for CLI colors in convert command."""

from __future__ import annotations

import pathlib

import pytest

from tmuxp._internal.private_path import PrivatePath
from tmuxp.cli._colors import ColorMode, Colors

# Convert command color output tests


def test_convert_success_message(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify success messages use success color (green)."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    result = colors.success("New workspace file saved to ")
    assert "\033[32m" in result  # green foreground
    assert "New workspace file saved to" in result


def test_convert_file_path_uses_info(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify file paths use info color (cyan)."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    path = "/path/to/config.yaml"
    result = colors.info(path)
    assert "\033[36m" in result  # cyan foreground
    assert path in result


def test_convert_format_type_highlighted(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify format type uses highlight color (magenta + bold)."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    for fmt in ["json", "yaml"]:
        result = colors.highlight(fmt)
        assert "\033[35m" in result  # magenta foreground
        assert "\033[1m" in result  # bold
        assert fmt in result


def test_convert_colors_disabled_plain_text() -> None:
    """Verify disabled colors return plain text."""
    colors = Colors(ColorMode.NEVER)

    assert colors.success("success") == "success"
    assert colors.info("info") == "info"
    assert colors.highlight("highlight") == "highlight"


def test_convert_combined_success_format(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify combined success + info format for save message."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    newfile = "/home/user/.tmuxp/session.json"
    output = (
        colors.success("New workspace file saved to ")
        + colors.info(f"<{newfile}>")
        + "."
    )
    # Should contain both green and cyan ANSI codes
    assert "\033[32m" in output  # green for success text
    assert "\033[36m" in output  # cyan for path
    assert "New workspace file saved to" in output
    assert newfile in output
    assert output.endswith(".")


def test_convert_prompt_format_with_highlight(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify prompt uses info for path and highlight for format."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    workspace_file = "/path/to/config.yaml"
    to_filetype = "json"
    prompt = (
        f"Convert {colors.info(workspace_file)} to {colors.highlight(to_filetype)}?"
    )
    assert "\033[36m" in prompt  # cyan for file path
    assert "\033[35m" in prompt  # magenta for format type
    assert workspace_file in prompt
    assert to_filetype in prompt


def test_convert_save_prompt_format(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify save prompt uses info color for new file path."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    newfile = "/path/to/config.json"
    prompt = f"Save workspace to {colors.info(newfile)}?"
    assert "\033[36m" in prompt  # cyan for file path
    assert newfile in prompt
    assert "Save workspace to" in prompt


# Privacy masking tests


def test_convert_masks_home_in_convert_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    """Convert should mask home directory in convert prompt."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: pathlib.Path("/home/testuser"))
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    workspace_file = pathlib.Path("/home/testuser/.tmuxp/session.yaml")
    prompt = f"Convert {colors.info(str(PrivatePath(workspace_file)))} to json?"

    assert "~/.tmuxp/session.yaml" in prompt
    assert "/home/testuser" not in prompt


def test_convert_masks_home_in_save_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    """Convert should mask home directory in save prompt."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: pathlib.Path("/home/testuser"))
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    newfile = pathlib.Path("/home/testuser/.tmuxp/session.json")
    prompt = f"Save workspace to {colors.info(str(PrivatePath(newfile)))}?"

    assert "~/.tmuxp/session.json" in prompt
    assert "/home/testuser" not in prompt


def test_convert_masks_home_in_saved_message(monkeypatch: pytest.MonkeyPatch) -> None:
    """Convert should mask home directory in saved message."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: pathlib.Path("/home/testuser"))
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    newfile = pathlib.Path("/home/testuser/.tmuxp/session.json")
    output = (
        colors.success("New workspace file saved to ")
        + colors.info(str(PrivatePath(newfile)))
        + "."
    )

    assert "~/.tmuxp/session.json" in output
    assert "/home/testuser" not in output
