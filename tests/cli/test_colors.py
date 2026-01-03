"""Tests for CLI color utilities."""

from __future__ import annotations

import sys

import pytest

from tmuxp.cli._colors import ColorMode, Colors, get_color_mode


class TestColorMode:
    """Tests for ColorMode enum and color detection."""

    def test_auto_tty_enabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Colors enabled when stdout is TTY in AUTO mode."""
        monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
        monkeypatch.delenv("NO_COLOR", raising=False)
        monkeypatch.delenv("FORCE_COLOR", raising=False)
        colors = Colors(ColorMode.AUTO)
        assert colors._enabled is True

    def test_auto_no_tty_disabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Colors disabled when stdout is not TTY in AUTO mode."""
        monkeypatch.setattr(sys.stdout, "isatty", lambda: False)
        monkeypatch.delenv("NO_COLOR", raising=False)
        monkeypatch.delenv("FORCE_COLOR", raising=False)
        colors = Colors(ColorMode.AUTO)
        assert colors._enabled is False

    def test_no_color_env_respected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """NO_COLOR environment variable disables colors even in ALWAYS mode."""
        monkeypatch.setenv("NO_COLOR", "1")
        colors = Colors(ColorMode.ALWAYS)
        assert colors._enabled is False

    def test_no_color_any_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """NO_COLOR with any non-empty value disables colors."""
        monkeypatch.setenv("NO_COLOR", "yes")
        colors = Colors(ColorMode.ALWAYS)
        assert colors._enabled is False

    def test_force_color_env_respected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """FORCE_COLOR environment variable enables colors in AUTO mode without TTY."""
        monkeypatch.setattr(sys.stdout, "isatty", lambda: False)
        monkeypatch.setenv("FORCE_COLOR", "1")
        monkeypatch.delenv("NO_COLOR", raising=False)
        colors = Colors(ColorMode.AUTO)
        assert colors._enabled is True

    def test_no_color_takes_precedence(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """NO_COLOR takes precedence over FORCE_COLOR."""
        monkeypatch.setenv("NO_COLOR", "1")
        monkeypatch.setenv("FORCE_COLOR", "1")
        colors = Colors(ColorMode.ALWAYS)
        assert colors._enabled is False

    def test_never_mode_disables(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """ColorMode.NEVER always disables colors."""
        monkeypatch.delenv("NO_COLOR", raising=False)
        colors = Colors(ColorMode.NEVER)
        assert colors._enabled is False
        # Output should be plain text without ANSI codes
        assert colors.success("test") == "test"
        assert colors.error("fail") == "fail"
        assert colors.warning("warn") == "warn"
        assert colors.info("info") == "info"
        assert colors.highlight("hl") == "hl"
        assert colors.muted("mute") == "mute"

    def test_always_mode_enables(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """ColorMode.ALWAYS enables colors (unless NO_COLOR set)."""
        monkeypatch.delenv("NO_COLOR", raising=False)
        colors = Colors(ColorMode.ALWAYS)
        assert colors._enabled is True
        # Output should contain ANSI escape codes
        assert "\033[" in colors.success("test")


class TestSemanticColors:
    """Tests for semantic color methods."""

    @pytest.fixture()
    def colors(self, monkeypatch: pytest.MonkeyPatch) -> Colors:
        """Create a Colors instance with colors enabled."""
        monkeypatch.delenv("NO_COLOR", raising=False)
        return Colors(ColorMode.ALWAYS)

    def test_success_applies_green(self, colors: Colors) -> None:
        """success() applies green color."""
        result = colors.success("ok")
        assert "\033[32m" in result  # green foreground
        assert "ok" in result
        assert result.endswith("\033[0m")  # reset at end

    def test_error_applies_red(self, colors: Colors) -> None:
        """error() applies red color."""
        result = colors.error("fail")
        assert "\033[31m" in result  # red foreground
        assert "fail" in result

    def test_warning_applies_yellow(self, colors: Colors) -> None:
        """warning() applies yellow color."""
        result = colors.warning("caution")
        assert "\033[33m" in result  # yellow foreground
        assert "caution" in result

    def test_info_applies_cyan(self, colors: Colors) -> None:
        """info() applies cyan color."""
        result = colors.info("message")
        assert "\033[36m" in result  # cyan foreground
        assert "message" in result

    def test_highlight_applies_magenta_bold(self, colors: Colors) -> None:
        """highlight() applies magenta color with bold by default."""
        result = colors.highlight("important")
        assert "\033[35m" in result  # magenta foreground
        assert "\033[1m" in result  # bold
        assert "important" in result

    def test_highlight_no_bold(self, colors: Colors) -> None:
        """highlight() can be used without bold."""
        result = colors.highlight("important", bold=False)
        assert "\033[35m" in result  # magenta foreground
        assert "\033[1m" not in result  # no bold
        assert "important" in result

    def test_muted_applies_blue(self, colors: Colors) -> None:
        """muted() applies blue color without bold."""
        result = colors.muted("secondary")
        assert "\033[34m" in result  # blue foreground
        assert "\033[1m" not in result  # never bold
        assert "secondary" in result

    def test_success_with_bold(self, colors: Colors) -> None:
        """success() can be used with bold."""
        result = colors.success("done", bold=True)
        assert "\033[32m" in result  # green
        assert "\033[1m" in result  # bold
        assert "done" in result


class TestGetColorMode:
    """Tests for get_color_mode function."""

    def test_none_returns_auto(self) -> None:
        """None argument returns AUTO mode."""
        assert get_color_mode(None) == ColorMode.AUTO

    def test_auto_string(self) -> None:
        """'auto' string returns AUTO mode."""
        assert get_color_mode("auto") == ColorMode.AUTO

    def test_always_string(self) -> None:
        """'always' string returns ALWAYS mode."""
        assert get_color_mode("always") == ColorMode.ALWAYS

    def test_never_string(self) -> None:
        """'never' string returns NEVER mode."""
        assert get_color_mode("never") == ColorMode.NEVER

    def test_case_insensitive(self) -> None:
        """Color mode strings are case insensitive."""
        assert get_color_mode("ALWAYS") == ColorMode.ALWAYS
        assert get_color_mode("Never") == ColorMode.NEVER
        assert get_color_mode("AUTO") == ColorMode.AUTO

    def test_invalid_returns_auto(self) -> None:
        """Invalid color mode strings return AUTO as fallback."""
        assert get_color_mode("invalid") == ColorMode.AUTO
        assert get_color_mode("yes") == ColorMode.AUTO
        assert get_color_mode("") == ColorMode.AUTO


class TestColorsClassAttributes:
    """Tests for Colors class color name attributes."""

    def test_semantic_color_names(self) -> None:
        """Verify semantic color name attributes exist."""
        assert Colors.SUCCESS == "green"
        assert Colors.WARNING == "yellow"
        assert Colors.ERROR == "red"
        assert Colors.INFO == "cyan"
        assert Colors.HIGHLIGHT == "magenta"
        assert Colors.MUTED == "blue"


class TestColorsDisabled:
    """Tests for Colors behavior when disabled."""

    def test_disabled_returns_plain_text(self) -> None:
        """When colors are disabled, methods return plain text."""
        colors = Colors(ColorMode.NEVER)
        assert colors.success("text") == "text"
        assert colors.error("text") == "text"
        assert colors.warning("text") == "text"
        assert colors.info("text") == "text"
        assert colors.highlight("text") == "text"
        assert colors.muted("text") == "text"

    def test_disabled_preserves_text(self) -> None:
        """Disabled colors preserve special characters."""
        colors = Colors(ColorMode.NEVER)
        special = "path/to/file.yaml"
        assert colors.info(special) == special

        with_spaces = "some message"
        assert colors.success(with_spaces) == with_spaces
