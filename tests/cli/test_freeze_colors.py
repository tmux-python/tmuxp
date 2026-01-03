"""Tests for CLI colors in freeze command."""

from __future__ import annotations

import pytest

from tmuxp.cli._colors import ColorMode, Colors


class TestFreezeColorOutput:
    """Tests for freeze command color output formatting."""

    @pytest.fixture()
    def colors(self, monkeypatch: pytest.MonkeyPatch) -> Colors:
        """Create a Colors instance with colors enabled."""
        monkeypatch.delenv("NO_COLOR", raising=False)
        return Colors(ColorMode.ALWAYS)

    @pytest.fixture()
    def colors_disabled(self) -> Colors:
        """Create a Colors instance with colors disabled."""
        return Colors(ColorMode.NEVER)

    def test_freeze_error_uses_red(self, colors: Colors) -> None:
        """Verify error messages use error color (red)."""
        msg = "Session not found"
        result = colors.error(msg)
        assert "\033[31m" in result  # red foreground
        assert msg in result
        assert result.endswith("\033[0m")  # reset at end

    def test_freeze_success_message(self, colors: Colors) -> None:
        """Verify success messages use success color (green)."""
        result = colors.success("Saved to ")
        assert "\033[32m" in result  # green foreground
        assert "Saved to" in result

    def test_freeze_file_path_uses_info(self, colors: Colors) -> None:
        """Verify file paths use info color (cyan)."""
        path = "/path/to/config.yaml"
        result = colors.info(path)
        assert "\033[36m" in result  # cyan foreground
        assert path in result

    def test_freeze_warning_file_exists(self, colors: Colors) -> None:
        """Verify file exists warning uses warning color (yellow)."""
        msg = "/path/to/config.yaml exists."
        result = colors.warning(msg)
        assert "\033[33m" in result  # yellow foreground
        assert msg in result

    def test_freeze_muted_for_secondary_text(self, colors: Colors) -> None:
        """Verify secondary text uses muted color (blue)."""
        msg = "Freeze does its best to snapshot live tmux sessions."
        result = colors.muted(msg)
        assert "\033[34m" in result  # blue foreground
        assert msg in result

    def test_freeze_colors_disabled_plain_text(self, colors_disabled: Colors) -> None:
        """Verify disabled colors return plain text."""
        assert colors_disabled.error("error") == "error"
        assert colors_disabled.success("success") == "success"
        assert colors_disabled.warning("warning") == "warning"
        assert colors_disabled.info("info") == "info"
        assert colors_disabled.muted("muted") == "muted"

    def test_freeze_combined_output_format(self, colors: Colors) -> None:
        """Verify combined success + info format for 'Saved to <path>' message."""
        dest = "/home/user/.tmuxp/session.yaml"
        output = colors.success("Saved to ") + colors.info(dest) + "."
        # Should contain both green and cyan ANSI codes
        assert "\033[32m" in output  # green for "Saved to"
        assert "\033[36m" in output  # cyan for path
        assert "Saved to" in output
        assert dest in output
        assert output.endswith(".")

    def test_freeze_warning_with_instructions(self, colors: Colors) -> None:
        """Verify warning + muted format for file exists message."""
        path = "/path/to/config.yaml"
        output = (
            colors.warning(f"{path} exists.")
            + " "
            + colors.muted("Pick a new filename.")
        )
        # Should contain both yellow and blue ANSI codes
        assert "\033[33m" in output  # yellow for warning
        assert "\033[34m" in output  # blue for muted
        assert path in output
        assert "Pick a new filename." in output

    def test_freeze_url_highlighted_in_help(self, colors: Colors) -> None:
        """Verify URLs use info color in help text."""
        url = "<http://tmuxp.git-pull.com/examples.html>"
        help_text = colors.muted("tmuxp has examples at ") + colors.info(url)
        assert "\033[34m" in help_text  # blue for muted text
        assert "\033[36m" in help_text  # cyan for URL
        assert url in help_text
