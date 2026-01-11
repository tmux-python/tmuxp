"""Tests for debug-info command color output and privacy masking."""

from __future__ import annotations

import pathlib

import pytest

from tests.cli.conftest import ANSI_BLUE, ANSI_BOLD, ANSI_CYAN, ANSI_MAGENTA
from tmuxp._internal.private_path import PrivatePath, collapse_home_in_string
from tmuxp.cli._colors import ColorMode, Colors

# Privacy masking in debug-info context


def test_debug_info_masks_home_in_paths(mock_home: pathlib.Path) -> None:
    """debug-info should mask home directory in paths."""
    # Simulate what debug-info does with tmuxp_path
    tmuxp_path = mock_home / "work/python/tmuxp/src/tmuxp"
    private_path = str(PrivatePath(tmuxp_path))

    assert private_path == "~/work/python/tmuxp/src/tmuxp"
    assert "/home/testuser" not in private_path


def test_debug_info_masks_home_in_system_path(mock_home: pathlib.Path) -> None:
    """debug-info should mask home directory in system PATH."""
    path_env = "/home/testuser/.local/bin:/usr/bin:/home/testuser/.cargo/bin"
    masked = collapse_home_in_string(path_env)

    assert masked == "~/.local/bin:/usr/bin:~/.cargo/bin"
    assert "/home/testuser" not in masked


def test_debug_info_preserves_system_paths(mock_home: pathlib.Path) -> None:
    """debug-info should preserve paths outside home directory."""
    tmux_path = "/usr/bin/tmux"
    private_path = str(PrivatePath(tmux_path))

    assert private_path == "/usr/bin/tmux"


# Formatting helpers in debug-info context


def test_debug_info_format_kv_labels(colors_always: Colors) -> None:
    """debug-info should highlight labels in key-value pairs."""
    result = colors_always.format_kv("tmux version", "3.2a")
    assert ANSI_MAGENTA in result  # magenta for label
    assert ANSI_BOLD in result  # bold for label
    assert "tmux version" in result
    assert "3.2a" in result


def test_debug_info_format_version(colors_always: Colors) -> None:
    """debug-info should highlight version strings."""
    result = colors_always.format_kv(
        "tmux version", colors_always.format_version("3.2a")
    )
    assert ANSI_CYAN in result  # cyan for version
    assert "3.2a" in result


def test_debug_info_format_path(colors_always: Colors) -> None:
    """debug-info should highlight paths."""
    result = colors_always.format_kv(
        "tmux path", colors_always.format_path("/usr/bin/tmux")
    )
    assert ANSI_CYAN in result  # cyan for path
    assert "/usr/bin/tmux" in result


def test_debug_info_format_separator(colors_always: Colors) -> None:
    """debug-info should use muted separators."""
    result = colors_always.format_separator()
    assert ANSI_BLUE in result  # blue for muted
    assert "-" * 25 in result


# tmux option formatting


def test_debug_info_format_tmux_option_space_sep(colors_always: Colors) -> None:
    """debug-info should format space-separated tmux options."""
    result = colors_always.format_tmux_option("status on")
    assert ANSI_MAGENTA in result  # magenta for key
    assert ANSI_CYAN in result  # cyan for value
    assert "status" in result
    assert "on" in result


def test_debug_info_format_tmux_option_equals_sep(colors_always: Colors) -> None:
    """debug-info should format equals-separated tmux options."""
    result = colors_always.format_tmux_option("base-index=0")
    assert ANSI_MAGENTA in result  # magenta for key
    assert ANSI_CYAN in result  # cyan for value
    assert "base-index" in result
    assert "0" in result


# Color mode behavior


def test_debug_info_respects_never_mode(colors_never: Colors) -> None:
    """debug-info should return plain text in NEVER mode."""
    result = colors_never.format_kv("tmux version", colors_never.format_version("3.2a"))
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
    colors_always: Colors,
    mock_home: pathlib.Path,
) -> None:
    """debug-info should combine privacy masking with color formatting."""
    # Simulate what debug-info does
    raw_path = mock_home / "work/tmuxp/src/tmuxp"
    private_path = str(PrivatePath(raw_path))
    formatted = colors_always.format_kv(
        "tmuxp path", colors_always.format_path(private_path)
    )

    assert "~/work/tmuxp/src/tmuxp" in formatted
    assert "/home/testuser" not in formatted
    assert ANSI_CYAN in formatted  # cyan for path
    assert ANSI_MAGENTA in formatted  # magenta for label


def test_debug_info_environment_section_format(colors_always: Colors) -> None:
    """debug-info environment section should have proper format."""
    # Simulate environment section format
    env_items = [
        f"\t{colors_always.format_kv('dist', 'Linux-6.6.87')}",
        f"\t{colors_always.format_kv('arch', 'x86_64')}",
    ]
    section = f"{colors_always.format_label('environment')}:\n" + "\n".join(env_items)

    assert "environment" in section
    assert "\t" in section  # indented items
    assert "dist" in section
    assert "arch" in section
