"""Integration tests for CLI color output across all commands."""

from __future__ import annotations

import sys
import typing as t

import pytest

from tmuxp.cli._colors import ColorMode, Colors, get_color_mode


class TestColorFlagIntegration:
    """Tests for --color flag integration across CLI."""

    def test_color_flag_auto_with_tty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify --color=auto enables colors when stdout is TTY."""
        monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
        monkeypatch.delenv("NO_COLOR", raising=False)
        monkeypatch.delenv("FORCE_COLOR", raising=False)

        color_mode = get_color_mode("auto")
        colors = Colors(color_mode)
        assert colors._enabled is True

    def test_color_flag_auto_without_tty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify --color=auto disables colors when stdout is not TTY."""
        monkeypatch.setattr(sys.stdout, "isatty", lambda: False)
        monkeypatch.delenv("NO_COLOR", raising=False)
        monkeypatch.delenv("FORCE_COLOR", raising=False)

        color_mode = get_color_mode("auto")
        colors = Colors(color_mode)
        assert colors._enabled is False

    def test_color_flag_always_forces_colors(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify --color=always forces colors even without TTY."""
        monkeypatch.setattr(sys.stdout, "isatty", lambda: False)
        monkeypatch.delenv("NO_COLOR", raising=False)

        color_mode = get_color_mode("always")
        colors = Colors(color_mode)
        assert colors._enabled is True
        # Verify output contains ANSI codes
        assert "\033[" in colors.success("test")

    def test_color_flag_never_disables_colors(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify --color=never disables colors even with TTY."""
        monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
        monkeypatch.delenv("NO_COLOR", raising=False)

        color_mode = get_color_mode("never")
        colors = Colors(color_mode)
        assert colors._enabled is False
        # Verify output is plain text
        assert colors.success("test") == "test"
        assert colors.error("test") == "test"
        assert colors.warning("test") == "test"


class TestEnvironmentVariableIntegration:
    """Tests for environment variable integration with color system."""

    def test_no_color_env_overrides_always(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify NO_COLOR environment variable overrides --color=always."""
        monkeypatch.setenv("NO_COLOR", "1")

        color_mode = get_color_mode("always")
        colors = Colors(color_mode)
        assert colors._enabled is False
        assert colors.success("test") == "test"

    def test_no_color_env_with_empty_value(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify empty NO_COLOR is ignored (per spec)."""
        monkeypatch.setenv("NO_COLOR", "")
        monkeypatch.delenv("FORCE_COLOR", raising=False)
        monkeypatch.setattr(sys.stdout, "isatty", lambda: True)

        colors = Colors(ColorMode.ALWAYS)
        # Empty NO_COLOR should be ignored, colors should be enabled
        assert colors._enabled is True

    def test_force_color_env_with_auto(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify FORCE_COLOR enables colors in auto mode without TTY."""
        monkeypatch.setattr(sys.stdout, "isatty", lambda: False)
        monkeypatch.setenv("FORCE_COLOR", "1")
        monkeypatch.delenv("NO_COLOR", raising=False)

        colors = Colors(ColorMode.AUTO)
        assert colors._enabled is True

    def test_no_color_takes_precedence_over_force_color(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify NO_COLOR takes precedence over FORCE_COLOR."""
        monkeypatch.setenv("NO_COLOR", "1")
        monkeypatch.setenv("FORCE_COLOR", "1")

        colors = Colors(ColorMode.ALWAYS)
        assert colors._enabled is False


class TestColorModeConsistency:
    """Tests verifying consistent color behavior across commands."""

    @pytest.fixture()
    def colors_enabled(self, monkeypatch: pytest.MonkeyPatch) -> Colors:
        """Create Colors with guaranteed enabled state."""
        monkeypatch.delenv("NO_COLOR", raising=False)
        return Colors(ColorMode.ALWAYS)

    @pytest.fixture()
    def colors_disabled(self) -> Colors:
        """Create Colors with guaranteed disabled state."""
        return Colors(ColorMode.NEVER)

    def test_all_semantic_methods_respect_enabled_state(
        self, colors_enabled: Colors
    ) -> None:
        """Verify all semantic color methods include ANSI codes when enabled."""
        methods: list[t.Callable[..., str]] = [
            colors_enabled.success,
            colors_enabled.error,
            colors_enabled.warning,
            colors_enabled.info,
            colors_enabled.muted,
        ]
        for method in methods:
            result = method("test")
            assert "\033[" in result, f"{method.__name__} should include ANSI codes"
            assert result.endswith("\033[0m"), f"{method.__name__} should reset color"

    def test_all_semantic_methods_respect_disabled_state(
        self, colors_disabled: Colors
    ) -> None:
        """Verify all semantic color methods return plain text when disabled."""
        methods: list[t.Callable[..., str]] = [
            colors_disabled.success,
            colors_disabled.error,
            colors_disabled.warning,
            colors_disabled.info,
            colors_disabled.muted,
        ]
        for method in methods:
            result = method("test")
            assert result == "test", f"{method.__name__} should return plain text"
            assert "\033[" not in result, (
                f"{method.__name__} should not have ANSI codes"
            )

    def test_highlight_bold_parameter(self, colors_enabled: Colors) -> None:
        """Verify highlight respects bold parameter."""
        with_bold = colors_enabled.highlight("test", bold=True)
        without_bold = colors_enabled.highlight("test", bold=False)

        assert "\033[1m" in with_bold
        assert "\033[1m" not in without_bold
        # Both should have magenta
        assert "\033[35m" in with_bold
        assert "\033[35m" in without_bold


class TestGetColorModeFunction:
    """Tests for get_color_mode helper function."""

    def test_none_defaults_to_auto(self) -> None:
        """Verify None input returns AUTO mode."""
        assert get_color_mode(None) == ColorMode.AUTO

    def test_valid_string_values(self) -> None:
        """Verify all valid string values are converted correctly."""
        assert get_color_mode("auto") == ColorMode.AUTO
        assert get_color_mode("always") == ColorMode.ALWAYS
        assert get_color_mode("never") == ColorMode.NEVER

    def test_case_insensitive(self) -> None:
        """Verify string values are case insensitive."""
        assert get_color_mode("AUTO") == ColorMode.AUTO
        assert get_color_mode("Always") == ColorMode.ALWAYS
        assert get_color_mode("NEVER") == ColorMode.NEVER
        assert get_color_mode("aUtO") == ColorMode.AUTO

    def test_invalid_values_fallback_to_auto(self) -> None:
        """Verify invalid values fallback to AUTO mode."""
        assert get_color_mode("invalid") == ColorMode.AUTO
        assert get_color_mode("yes") == ColorMode.AUTO
        assert get_color_mode("no") == ColorMode.AUTO
        assert get_color_mode("true") == ColorMode.AUTO
        assert get_color_mode("") == ColorMode.AUTO
