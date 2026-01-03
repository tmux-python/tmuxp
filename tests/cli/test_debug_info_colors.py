"""Tests for debug-info command color output and privacy masking."""

from __future__ import annotations

import pathlib

import pytest

from tmuxp._internal.private_path import PrivatePath, collapse_home_in_string
from tmuxp.cli._colors import ColorMode, Colors

# Privacy masking in debug-info context


def test_debug_info_masks_home_in_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    """debug-info should mask home directory in paths."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: pathlib.Path("/home/testuser"))

    # Simulate what debug-info does with tmuxp_path
    tmuxp_path = pathlib.Path("/home/testuser/work/python/tmuxp/src/tmuxp")
    private_path = str(PrivatePath(tmuxp_path))

    assert private_path == "~/work/python/tmuxp/src/tmuxp"
    assert "/home/testuser" not in private_path


def test_debug_info_masks_home_in_system_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """debug-info should mask home directory in system PATH."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: pathlib.Path("/home/testuser"))

    path_env = "/home/testuser/.local/bin:/usr/bin:/home/testuser/.cargo/bin"
    masked = collapse_home_in_string(path_env)

    assert masked == "~/.local/bin:/usr/bin:~/.cargo/bin"
    assert "/home/testuser" not in masked


def test_debug_info_preserves_system_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    """debug-info should preserve paths outside home directory."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: pathlib.Path("/home/testuser"))

    tmux_path = "/usr/bin/tmux"
    private_path = str(PrivatePath(tmux_path))

    assert private_path == "/usr/bin/tmux"


# Formatting helpers in debug-info context


def test_debug_info_format_kv_labels(monkeypatch: pytest.MonkeyPatch) -> None:
    """debug-info should highlight labels in key-value pairs."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    result = colors.format_kv("tmux version", "3.2a")
    assert "\033[35m" in result  # magenta for label
    assert "\033[1m" in result  # bold for label
    assert "tmux version" in result
    assert "3.2a" in result


def test_debug_info_format_version(monkeypatch: pytest.MonkeyPatch) -> None:
    """debug-info should highlight version strings."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    result = colors.format_kv("tmux version", colors.format_version("3.2a"))
    assert "\033[36m" in result  # cyan for version
    assert "3.2a" in result


def test_debug_info_format_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """debug-info should highlight paths."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    result = colors.format_kv("tmux path", colors.format_path("/usr/bin/tmux"))
    assert "\033[36m" in result  # cyan for path
    assert "/usr/bin/tmux" in result


def test_debug_info_format_separator(monkeypatch: pytest.MonkeyPatch) -> None:
    """debug-info should use muted separators."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    result = colors.format_separator()
    assert "\033[34m" in result  # blue for muted
    assert "-" * 25 in result


# tmux option formatting


def test_debug_info_format_tmux_option_space_sep(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """debug-info should format space-separated tmux options."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    result = colors.format_tmux_option("status on")
    assert "\033[35m" in result  # magenta for key
    assert "\033[36m" in result  # cyan for value
    assert "status" in result
    assert "on" in result


def test_debug_info_format_tmux_option_equals_sep(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """debug-info should format equals-separated tmux options."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    result = colors.format_tmux_option("base-index=0")
    assert "\033[35m" in result  # magenta for key
    assert "\033[36m" in result  # cyan for value
    assert "base-index" in result
    assert "0" in result


# Color mode behavior


def test_debug_info_respects_never_mode() -> None:
    """debug-info should return plain text in NEVER mode."""
    colors = Colors(ColorMode.NEVER)

    result = colors.format_kv("tmux version", colors.format_version("3.2a"))
    assert "\033[" not in result
    assert result == "tmux version: 3.2a"


def test_debug_info_respects_no_color_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """debug-info should respect NO_COLOR environment variable."""
    monkeypatch.setenv("NO_COLOR", "1")
    colors = Colors(ColorMode.ALWAYS)

    result = colors.format_kv("tmux path", "/usr/bin/tmux")
    assert "\033[" not in result
    assert result == "tmux path: /usr/bin/tmux"


# Combined formatting


def test_debug_info_combined_path_with_privacy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """debug-info should combine privacy masking with color formatting."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: pathlib.Path("/home/testuser"))
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    # Simulate what debug-info does
    raw_path = "/home/testuser/work/tmuxp/src/tmuxp"
    private_path = str(PrivatePath(raw_path))
    formatted = colors.format_kv("tmuxp path", colors.format_path(private_path))

    assert "~/work/tmuxp/src/tmuxp" in formatted
    assert "/home/testuser" not in formatted
    assert "\033[36m" in formatted  # cyan for path
    assert "\033[35m" in formatted  # magenta for label


def test_debug_info_environment_section_format(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """debug-info environment section should have proper format."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    # Simulate environment section format
    env_items = [
        f"\t{colors.format_kv('dist', 'Linux-6.6.87')}",
        f"\t{colors.format_kv('arch', 'x86_64')}",
    ]
    section = f"{colors.format_label('environment')}:\n" + "\n".join(env_items)

    assert "environment" in section
    assert "\t" in section  # indented items
    assert "dist" in section
    assert "arch" in section
