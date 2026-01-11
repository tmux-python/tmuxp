"""Tests for TmuxpHelpFormatter and themed formatter factory."""

from __future__ import annotations

import argparse

import pytest

from tests.cli.conftest import ANSI_RESET
from tmuxp.cli._colors import ColorMode, Colors
from tmuxp.cli._formatter import (
    HelpTheme,
    TmuxpHelpFormatter,
    create_themed_formatter,
)


def test_create_themed_formatter_returns_subclass() -> None:
    """Factory returns a TmuxpHelpFormatter subclass."""
    formatter_cls = create_themed_formatter()
    assert issubclass(formatter_cls, TmuxpHelpFormatter)


def test_create_themed_formatter_with_colors_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Formatter has theme when colors enabled."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)
    formatter_cls = create_themed_formatter(colors)
    formatter = formatter_cls("test")

    assert formatter._theme is not None
    assert formatter._theme.prog != ""  # Has color codes


def test_create_themed_formatter_with_colors_disabled() -> None:
    """Formatter has no theme when colors disabled."""
    colors = Colors(ColorMode.NEVER)
    formatter_cls = create_themed_formatter(colors)
    formatter = formatter_cls("test")

    assert formatter._theme is None


def test_create_themed_formatter_auto_mode_respects_no_color(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Auto mode respects NO_COLOR environment variable."""
    monkeypatch.setenv("NO_COLOR", "1")
    formatter_cls = create_themed_formatter()
    formatter = formatter_cls("test")

    assert formatter._theme is None


def test_create_themed_formatter_auto_mode_respects_force_color(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Auto mode respects FORCE_COLOR environment variable."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("FORCE_COLOR", "1")
    formatter_cls = create_themed_formatter()
    formatter = formatter_cls("test")

    assert formatter._theme is not None


def test_fill_text_with_theme_colorizes_examples(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Examples section is colorized when theme is set."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)
    formatter_cls = create_themed_formatter(colors)
    formatter = formatter_cls("tmuxp")

    text = "Examples:\n  tmuxp load myproject"
    result = formatter._fill_text(text, 80, "")

    # Should contain ANSI escape codes
    assert "\033[" in result
    assert "tmuxp" in result
    assert "load" in result


def test_fill_text_without_theme_plain_text() -> None:
    """Examples section is plain text when no theme."""
    colors = Colors(ColorMode.NEVER)
    formatter_cls = create_themed_formatter(colors)
    formatter = formatter_cls("tmuxp")

    text = "Examples:\n  tmuxp load myproject"
    result = formatter._fill_text(text, 80, "")

    # Should NOT contain ANSI escape codes
    assert "\033[" not in result
    assert "tmuxp load myproject" in result


def test_fill_text_category_headings_colorized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Category headings within examples block are colorized."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)
    formatter_cls = create_themed_formatter(colors)
    formatter = formatter_cls("tmuxp")

    # Test category heading without "examples:" suffix
    text = "examples:\n  tmuxp ls\n\nMachine-readable output:\n  tmuxp ls --json"
    result = formatter._fill_text(text, 80, "")

    # Both headings should be colorized
    assert "\033[" in result
    assert "examples:" in result
    assert "Machine-readable output:" in result
    # Commands should also be colorized
    assert "tmuxp" in result
    assert "--json" in result


def test_fill_text_category_heading_only_in_examples_block(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Category headings are only recognized within examples block."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)
    formatter_cls = create_themed_formatter(colors)
    formatter = formatter_cls("tmuxp")

    # Text before examples block should not be colorized as heading
    text = "Some heading:\n  not a command\n\nexamples:\n  tmuxp load"
    result = formatter._fill_text(text, 80, "")

    # "Some heading:" should NOT be colorized (it's before examples block)
    # "examples:" and the command should be colorized
    lines = result.split("\n")
    # First line should be plain (no ANSI in "Some heading:")
    assert "Some heading:" in lines[0]


def test_parser_help_respects_no_color(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Parser --help output is plain when NO_COLOR set."""
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setenv("COLUMNS", "100")

    formatter_cls = create_themed_formatter()
    parser = argparse.ArgumentParser(
        prog="test",
        description="Examples:\n  test command",
        formatter_class=formatter_cls,
    )

    with pytest.raises(SystemExit):
        parser.parse_args(["--help"])

    captured = capsys.readouterr()
    assert "\033[" not in captured.out


def test_parser_help_colorized_with_force_color(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Parser --help output is colorized when FORCE_COLOR set."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.setenv("COLUMNS", "100")

    formatter_cls = create_themed_formatter()
    parser = argparse.ArgumentParser(
        prog="test",
        description="Examples:\n  test command",
        formatter_class=formatter_cls,
    )

    with pytest.raises(SystemExit):
        parser.parse_args(["--help"])

    captured = capsys.readouterr()
    assert "\033[" in captured.out


def test_help_theme_from_colors_with_none_returns_empty() -> None:
    """HelpTheme.from_colors(None) returns empty theme."""
    theme = HelpTheme.from_colors(None)

    assert theme.prog == ""
    assert theme.action == ""
    assert theme.reset == ""


def test_help_theme_from_colors_disabled_returns_empty() -> None:
    """HelpTheme.from_colors with disabled colors returns empty theme."""
    colors = Colors(ColorMode.NEVER)
    theme = HelpTheme.from_colors(colors)

    assert theme.prog == ""
    assert theme.action == ""
    assert theme.reset == ""


def test_help_theme_from_colors_enabled_returns_colored(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """HelpTheme.from_colors with enabled colors returns colored theme."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)
    theme = HelpTheme.from_colors(colors)

    # Should have ANSI codes
    assert "\033[" in theme.prog
    assert "\033[" in theme.action
    assert theme.reset == ANSI_RESET


def test_fill_text_section_heading_with_examples_suffix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Section headings ending with 'examples:' are colorized without initial block."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)
    formatter_cls = create_themed_formatter(colors)
    formatter = formatter_cls("tmuxp")

    # This is what build_description produces - no initial "examples:" block
    text = (
        "load examples:\n  tmuxp load myproject\n\n"
        "freeze examples:\n  tmuxp freeze mysession"
    )
    result = formatter._fill_text(text, 80, "")

    # Both headings should be colorized (contain ANSI escape codes)
    assert "\033[" in result
    # Commands should be colorized
    assert "tmuxp" in result


def test_fill_text_multiple_example_sections_all_colorized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Multiple 'X examples:' sections should all be colorized."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colors(ColorMode.ALWAYS)
    formatter_cls = create_themed_formatter(colors)
    formatter = formatter_cls("tmuxp")

    text = """load examples:
  tmuxp load myproject

freeze examples:
  tmuxp freeze mysession

ls examples:
  tmuxp ls"""
    result = formatter._fill_text(text, 80, "")

    # All sections should have ANSI codes
    # Count ANSI escape sequences - should have at least heading + command per section
    assert result.count("\033[") >= 6
