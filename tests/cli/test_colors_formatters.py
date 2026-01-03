"""Tests for Colors class formatting helper methods."""

from __future__ import annotations

import pytest

from tmuxp.cli._colors import ColorMode, Colors

# format_label tests


def test_format_label_plain_text() -> None:
    """format_label returns plain text when colors disabled."""
    colors = Colors(ColorMode.NEVER)
    assert colors.format_label("tmux path") == "tmux path"


def test_format_label_applies_highlight(monkeypatch: pytest.MonkeyPatch) -> None:
    """format_label applies highlight (bold magenta) when enabled."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    result = colors.format_label("tmux path")
    assert "\033[35m" in result  # magenta
    assert "\033[1m" in result  # bold
    assert "tmux path" in result


# format_path tests


def test_format_path_plain_text() -> None:
    """format_path returns plain text when colors disabled."""
    colors = Colors(ColorMode.NEVER)
    assert colors.format_path("/usr/bin/tmux") == "/usr/bin/tmux"


def test_format_path_applies_info(monkeypatch: pytest.MonkeyPatch) -> None:
    """format_path applies info color (cyan) when enabled."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    result = colors.format_path("/usr/bin/tmux")
    assert "\033[36m" in result  # cyan
    assert "/usr/bin/tmux" in result


# format_version tests


def test_format_version_plain_text() -> None:
    """format_version returns plain text when colors disabled."""
    colors = Colors(ColorMode.NEVER)
    assert colors.format_version("3.2a") == "3.2a"


def test_format_version_applies_info(monkeypatch: pytest.MonkeyPatch) -> None:
    """format_version applies info color (cyan) when enabled."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    result = colors.format_version("3.2a")
    assert "\033[36m" in result  # cyan
    assert "3.2a" in result


# format_separator tests


def test_format_separator_default_length() -> None:
    """format_separator creates 25-character separator by default."""
    colors = Colors(ColorMode.NEVER)
    result = colors.format_separator()
    assert result == "-" * 25


def test_format_separator_custom_length() -> None:
    """format_separator respects custom length."""
    colors = Colors(ColorMode.NEVER)
    assert colors.format_separator(10) == "-" * 10
    assert colors.format_separator(50) == "-" * 50


def test_format_separator_applies_muted(monkeypatch: pytest.MonkeyPatch) -> None:
    """format_separator applies muted color (blue) when enabled."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    result = colors.format_separator()
    assert "\033[34m" in result  # blue
    assert "-" * 25 in result


# format_kv tests


def test_format_kv_plain_text() -> None:
    """format_kv returns plain key: value when colors disabled."""
    colors = Colors(ColorMode.NEVER)
    assert colors.format_kv("tmux version", "3.2a") == "tmux version: 3.2a"


def test_format_kv_highlights_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """format_kv highlights the key but not the value."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    result = colors.format_kv("tmux version", "3.2a")
    assert "\033[35m" in result  # magenta for key
    assert "\033[1m" in result  # bold for key
    assert "tmux version" in result
    assert ": 3.2a" in result


def test_format_kv_empty_value() -> None:
    """format_kv handles empty value."""
    colors = Colors(ColorMode.NEVER)
    assert colors.format_kv("environment", "") == "environment: "


# format_tmux_option tests


def test_format_tmux_option_plain_text_key_value() -> None:
    """format_tmux_option returns plain text when colors disabled (key=value)."""
    colors = Colors(ColorMode.NEVER)
    assert colors.format_tmux_option("base-index=1") == "base-index=1"


def test_format_tmux_option_plain_text_space_sep() -> None:
    """format_tmux_option returns plain text when colors disabled (space-sep)."""
    colors = Colors(ColorMode.NEVER)
    assert colors.format_tmux_option("status on") == "status on"


def test_format_tmux_option_key_value_format(monkeypatch: pytest.MonkeyPatch) -> None:
    """format_tmux_option highlights key=value format."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    result = colors.format_tmux_option("base-index=1")
    assert "\033[35m" in result  # magenta for key
    assert "\033[36m" in result  # cyan for value
    assert "base-index" in result
    assert "=1" in result or "1" in result


def test_format_tmux_option_space_separated(monkeypatch: pytest.MonkeyPatch) -> None:
    """format_tmux_option highlights space-separated format."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    result = colors.format_tmux_option("status on")
    assert "\033[35m" in result  # magenta for key
    assert "\033[36m" in result  # cyan for value
    assert "status" in result
    assert "on" in result


def test_format_tmux_option_single_word() -> None:
    """format_tmux_option returns single words unchanged."""
    colors = Colors(ColorMode.NEVER)
    assert colors.format_tmux_option("default") == "default"


def test_format_tmux_option_empty() -> None:
    """format_tmux_option handles empty string."""
    colors = Colors(ColorMode.NEVER)
    assert colors.format_tmux_option("") == ""


def test_format_tmux_option_value_with_spaces(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """format_tmux_option handles values containing spaces."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    # tmux options can have values with spaces like status-left "string here"
    result = colors.format_tmux_option('status-left "#S: #W"')
    assert "status-left" in result
    assert '"#S: #W"' in result


def test_format_tmux_option_value_with_equals(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """format_tmux_option handles values containing equals signs."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)

    # Only split on first equals
    result = colors.format_tmux_option("command=echo a=b")
    assert "command" in result
    assert "echo a=b" in result
