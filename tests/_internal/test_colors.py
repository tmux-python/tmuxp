"""Tests for _internal color utilities."""

from __future__ import annotations

import sys

import pytest

from tests._internal.conftest import (
    ANSI_BLUE,
    ANSI_BOLD,
    ANSI_BRIGHT_CYAN,
    ANSI_CYAN,
    ANSI_GREEN,
    ANSI_MAGENTA,
    ANSI_RED,
    ANSI_RESET,
    ANSI_YELLOW,
)
from tmuxp._internal.colors import (
    ColorMode,
    Colors,
    UnknownStyleColor,
    build_description,
    get_color_mode,
    style,
)

# ColorMode tests


def test_auto_tty_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Colors enabled when stdout is TTY in AUTO mode."""
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    colors = Colors(ColorMode.AUTO)
    assert colors._enabled is True


def test_auto_no_tty_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Colors disabled when stdout is not TTY in AUTO mode."""
    monkeypatch.setattr(sys.stdout, "isatty", lambda: False)
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    colors = Colors(ColorMode.AUTO)
    assert colors._enabled is False


def test_no_color_env_respected(monkeypatch: pytest.MonkeyPatch) -> None:
    """NO_COLOR environment variable disables colors even in ALWAYS mode."""
    monkeypatch.setenv("NO_COLOR", "1")
    colors = Colors(ColorMode.ALWAYS)
    assert colors._enabled is False


def test_no_color_any_value(monkeypatch: pytest.MonkeyPatch) -> None:
    """NO_COLOR with any non-empty value disables colors."""
    monkeypatch.setenv("NO_COLOR", "yes")
    colors = Colors(ColorMode.ALWAYS)
    assert colors._enabled is False


def test_force_color_env_respected(monkeypatch: pytest.MonkeyPatch) -> None:
    """FORCE_COLOR environment variable enables colors in AUTO mode without TTY."""
    monkeypatch.setattr(sys.stdout, "isatty", lambda: False)
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.AUTO)
    assert colors._enabled is True


def test_no_color_takes_precedence(monkeypatch: pytest.MonkeyPatch) -> None:
    """NO_COLOR takes precedence over FORCE_COLOR."""
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setenv("FORCE_COLOR", "1")
    colors = Colors(ColorMode.ALWAYS)
    assert colors._enabled is False


def test_never_mode_disables(monkeypatch: pytest.MonkeyPatch) -> None:
    """ColorMode.NEVER always disables colors."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.NEVER)
    assert colors._enabled is False
    assert colors.success("test") == "test"
    assert colors.error("fail") == "fail"
    assert colors.warning("warn") == "warn"
    assert colors.info("info") == "info"
    assert colors.highlight("hl") == "hl"
    assert colors.muted("mute") == "mute"


def test_always_mode_enables(monkeypatch: pytest.MonkeyPatch) -> None:
    """ColorMode.ALWAYS enables colors (unless NO_COLOR set)."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)
    assert colors._enabled is True
    assert "\033[" in colors.success("test")


# Semantic color tests


def test_success_applies_green(monkeypatch: pytest.MonkeyPatch) -> None:
    """success() applies green color."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)
    result = colors.success("ok")
    assert ANSI_GREEN in result
    assert "ok" in result
    assert result.endswith(ANSI_RESET)


def test_error_applies_red(monkeypatch: pytest.MonkeyPatch) -> None:
    """error() applies red color."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)
    result = colors.error("fail")
    assert ANSI_RED in result
    assert "fail" in result


def test_warning_applies_yellow(monkeypatch: pytest.MonkeyPatch) -> None:
    """warning() applies yellow color."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)
    result = colors.warning("caution")
    assert ANSI_YELLOW in result
    assert "caution" in result


def test_info_applies_cyan(monkeypatch: pytest.MonkeyPatch) -> None:
    """info() applies cyan color."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)
    result = colors.info("message")
    assert ANSI_CYAN in result
    assert "message" in result


def test_highlight_applies_magenta_bold(monkeypatch: pytest.MonkeyPatch) -> None:
    """highlight() applies magenta color with bold by default."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)
    result = colors.highlight("important")
    assert ANSI_MAGENTA in result
    assert ANSI_BOLD in result
    assert "important" in result


def test_highlight_no_bold(monkeypatch: pytest.MonkeyPatch) -> None:
    """highlight() can be used without bold."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)
    result = colors.highlight("important", bold=False)
    assert ANSI_MAGENTA in result
    assert ANSI_BOLD not in result
    assert "important" in result


def test_muted_applies_blue(monkeypatch: pytest.MonkeyPatch) -> None:
    """muted() applies blue color without bold."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)
    result = colors.muted("secondary")
    assert ANSI_BLUE in result
    assert ANSI_BOLD not in result
    assert "secondary" in result


def test_success_with_bold(monkeypatch: pytest.MonkeyPatch) -> None:
    """success() can be used with bold."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)
    result = colors.success("done", bold=True)
    assert ANSI_GREEN in result
    assert ANSI_BOLD in result
    assert "done" in result


# get_color_mode tests


def test_get_color_mode_none_returns_auto() -> None:
    """None argument returns AUTO mode."""
    assert get_color_mode(None) == ColorMode.AUTO


def test_get_color_mode_auto_string() -> None:
    """'auto' string returns AUTO mode."""
    assert get_color_mode("auto") == ColorMode.AUTO


def test_get_color_mode_always_string() -> None:
    """'always' string returns ALWAYS mode."""
    assert get_color_mode("always") == ColorMode.ALWAYS


def test_get_color_mode_never_string() -> None:
    """'never' string returns NEVER mode."""
    assert get_color_mode("never") == ColorMode.NEVER


def test_get_color_mode_case_insensitive() -> None:
    """Color mode strings are case insensitive."""
    assert get_color_mode("ALWAYS") == ColorMode.ALWAYS
    assert get_color_mode("Never") == ColorMode.NEVER
    assert get_color_mode("AUTO") == ColorMode.AUTO


def test_get_color_mode_invalid_returns_auto() -> None:
    """Invalid color mode strings return AUTO as fallback."""
    assert get_color_mode("invalid") == ColorMode.AUTO
    assert get_color_mode("yes") == ColorMode.AUTO
    assert get_color_mode("") == ColorMode.AUTO


# Colors class attribute tests


def test_semantic_color_names() -> None:
    """Verify semantic color name attributes exist."""
    assert Colors.SUCCESS == "green"
    assert Colors.WARNING == "yellow"
    assert Colors.ERROR == "red"
    assert Colors.INFO == "cyan"
    assert Colors.HIGHLIGHT == "magenta"
    assert Colors.MUTED == "blue"


# Colors disabled tests


def test_disabled_returns_plain_text() -> None:
    """When colors are disabled, methods return plain text."""
    colors = Colors(ColorMode.NEVER)
    assert colors.success("text") == "text"
    assert colors.error("text") == "text"
    assert colors.warning("text") == "text"
    assert colors.info("text") == "text"
    assert colors.highlight("text") == "text"
    assert colors.muted("text") == "text"


def test_disabled_preserves_text() -> None:
    """Disabled colors preserve special characters."""
    colors = Colors(ColorMode.NEVER)
    special = "path/to/file.yaml"
    assert colors.info(special) == special

    with_spaces = "some message"
    assert colors.success(with_spaces) == with_spaces


# RGB tuple validation tests


def test_style_with_valid_rgb_tuple() -> None:
    """style() should accept valid RGB tuple."""
    result = style("test", fg=(255, 128, 0))
    assert "\033[38;2;255;128;0m" in result
    assert "test" in result


def test_style_with_invalid_2_element_tuple() -> None:
    """style() should raise UnknownStyleColor for 2-element tuple."""
    with pytest.raises(UnknownStyleColor):
        style("test", fg=(255, 128))  # type: ignore[arg-type]


def test_style_with_invalid_4_element_tuple() -> None:
    """style() should raise UnknownStyleColor for 4-element tuple."""
    with pytest.raises(UnknownStyleColor):
        style("test", fg=(255, 128, 0, 64))  # type: ignore[arg-type]


def test_style_with_empty_tuple() -> None:
    """style() treats empty tuple as 'no color' (falsy value)."""
    result = style("test", fg=())  # type: ignore[arg-type]
    # Empty tuple is falsy, so no fg color is applied
    assert "test" in result
    assert "\033[38" not in result  # No foreground color escape


def test_style_with_rgb_value_too_high() -> None:
    """style() should reject RGB values > 255."""
    with pytest.raises(UnknownStyleColor):
        style("test", fg=(256, 0, 0))


def test_style_with_rgb_value_negative() -> None:
    """style() should reject negative RGB values."""
    with pytest.raises(UnknownStyleColor):
        style("test", fg=(-1, 128, 0))


def test_style_with_rgb_non_integer() -> None:
    """style() should reject non-integer RGB values."""
    with pytest.raises(UnknownStyleColor):
        style("test", fg=(255.5, 128, 0))  # type: ignore[arg-type]


# heading() method tests


def test_heading_applies_bright_cyan_bold(monkeypatch: pytest.MonkeyPatch) -> None:
    """heading() applies bright_cyan with bold when colors are enabled."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)
    result = colors.heading("Local workspaces:")
    assert ANSI_BRIGHT_CYAN in result
    assert ANSI_BOLD in result
    assert "Local workspaces:" in result
    assert ANSI_RESET in result


# build_description tests


def test_build_description_named_heading_includes_examples_suffix() -> None:
    """Named heading should include 'examples:' suffix for formatter detection."""
    result = build_description("My tool.", [("sync", ["mytool sync repo"])])

    # Should be "sync examples:" not just "sync:"
    assert "sync examples:" in result
    # Verify the old format is not present (unless contained in "sync examples:")
    lines = result.split("\n")
    heading_line = next(line for line in lines if "sync" in line.lower())
    assert heading_line == "sync examples:"


def test_build_description_no_heading_uses_examples() -> None:
    """Heading=None should produce bare 'examples:' title."""
    result = build_description("My tool.", [(None, ["mytool run"])])

    assert "examples:" in result
    assert result.count("examples:") == 1  # Just one


def test_build_description_multiple_named_headings() -> None:
    """Multiple named headings should all have 'examples:' suffix."""
    result = build_description(
        "My tool.",
        [
            ("load", ["mytool load"]),
            ("freeze", ["mytool freeze"]),
            ("ls", ["mytool ls"]),
        ],
    )

    assert "load examples:" in result
    assert "freeze examples:" in result
    assert "ls examples:" in result


def test_build_description_empty_intro() -> None:
    """Empty intro should not add blank sections."""
    result = build_description("", [(None, ["cmd"])])

    assert result.startswith("examples:")
    assert "cmd" in result
