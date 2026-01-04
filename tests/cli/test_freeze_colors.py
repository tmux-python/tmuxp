"""Tests for CLI colors in freeze command."""

from __future__ import annotations

import pathlib

import pytest

from tmuxp._internal.private_path import PrivatePath
from tmuxp.cli._colors import ColorMode, Colors

# Freeze command color output tests


def test_freeze_error_uses_red(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify error messages use error color (red)."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    msg = "Session not found"
    result = colors.error(msg)
    assert "\033[31m" in result  # red foreground
    assert msg in result
    assert result.endswith("\033[0m")  # reset at end


def test_freeze_success_message(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify success messages use success color (green)."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    result = colors.success("Saved to ")
    assert "\033[32m" in result  # green foreground
    assert "Saved to" in result


def test_freeze_file_path_uses_info(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify file paths use info color (cyan)."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    path = "/path/to/config.yaml"
    result = colors.info(path)
    assert "\033[36m" in result  # cyan foreground
    assert path in result


def test_freeze_warning_file_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify file exists warning uses warning color (yellow)."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    msg = "/path/to/config.yaml exists."
    result = colors.warning(msg)
    assert "\033[33m" in result  # yellow foreground
    assert msg in result


def test_freeze_muted_for_secondary_text(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify secondary text uses muted color (blue)."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    msg = "Freeze does its best to snapshot live tmux sessions."
    result = colors.muted(msg)
    assert "\033[34m" in result  # blue foreground
    assert msg in result


def test_freeze_colors_disabled_plain_text() -> None:
    """Verify disabled colors return plain text."""
    colors = Colors(ColorMode.NEVER)

    assert colors.error("error") == "error"
    assert colors.success("success") == "success"
    assert colors.warning("warning") == "warning"
    assert colors.info("info") == "info"
    assert colors.muted("muted") == "muted"


def test_freeze_combined_output_format(monkeypatch: pytest.MonkeyPatch) -> None:
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


def test_freeze_warning_with_instructions(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify warning + muted format for file exists message."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    path = "/path/to/config.yaml"
    output = (
        colors.warning(f"{path} exists.") + " " + colors.muted("Pick a new filename.")
    )
    # Should contain both yellow and blue ANSI codes
    assert "\033[33m" in output  # yellow for warning
    assert "\033[34m" in output  # blue for muted
    assert path in output
    assert "Pick a new filename." in output


def test_freeze_url_highlighted_in_help(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify URLs use info color in help text."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    url = "<http://tmuxp.git-pull.com/examples.html>"
    help_text = colors.muted("tmuxp has examples at ") + colors.info(url)
    assert "\033[34m" in help_text  # blue for muted text
    assert "\033[36m" in help_text  # cyan for URL
    assert url in help_text


# Privacy masking tests


def test_freeze_masks_home_in_saved_message(monkeypatch: pytest.MonkeyPatch) -> None:
    """Freeze should mask home directory in 'Saved to' message."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: pathlib.Path("/home/testuser"))
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    dest = "/home/testuser/.tmuxp/session.yaml"
    output = colors.success("Saved to ") + colors.info(str(PrivatePath(dest))) + "."

    assert "~/.tmuxp/session.yaml" in output
    assert "/home/testuser" not in output


def test_freeze_masks_home_in_exists_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    """Freeze should mask home directory in 'exists' warning."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: pathlib.Path("/home/testuser"))
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    dest_prompt = "/home/testuser/.tmuxp/session.yaml"
    output = colors.warning(f"{PrivatePath(dest_prompt)} exists.")

    assert "~/.tmuxp/session.yaml exists." in output
    assert "/home/testuser" not in output
