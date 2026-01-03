"""Tests for CLI colors in import command."""

from __future__ import annotations

import pytest

from tmuxp.cli._colors import ColorMode, Colors


class TestImportColorOutput:
    """Tests for import command color output formatting."""

    @pytest.fixture()
    def colors(self, monkeypatch: pytest.MonkeyPatch) -> Colors:
        """Create a Colors instance with colors enabled."""
        monkeypatch.delenv("NO_COLOR", raising=False)
        return Colors(ColorMode.ALWAYS)

    @pytest.fixture()
    def colors_disabled(self) -> Colors:
        """Create a Colors instance with colors disabled."""
        return Colors(ColorMode.NEVER)

    def test_import_error_unknown_format(self, colors: Colors) -> None:
        """Verify unknown format error uses error color (red)."""
        msg = "Unknown config format."
        result = colors.error(msg)
        assert "\033[31m" in result  # red foreground
        assert msg in result
        assert result.endswith("\033[0m")  # reset at end

    def test_import_success_message(self, colors: Colors) -> None:
        """Verify success messages use success color (green)."""
        result = colors.success("Saved to ")
        assert "\033[32m" in result  # green foreground
        assert "Saved to" in result

    def test_import_file_path_uses_info(self, colors: Colors) -> None:
        """Verify file paths use info color (cyan)."""
        path = "/path/to/config.yaml"
        result = colors.info(path)
        assert "\033[36m" in result  # cyan foreground
        assert path in result

    def test_import_muted_for_banner(self, colors: Colors) -> None:
        """Verify banner text uses muted color (blue)."""
        msg = "Configuration import does its best to convert files."
        result = colors.muted(msg)
        assert "\033[34m" in result  # blue foreground
        assert msg in result

    def test_import_muted_for_separator(self, colors: Colors) -> None:
        """Verify separator uses muted color (blue)."""
        separator = "---------------------------------------------------------------"
        result = colors.muted(separator)
        assert "\033[34m" in result  # blue foreground
        assert separator in result

    def test_import_colors_disabled_plain_text(self, colors_disabled: Colors) -> None:
        """Verify disabled colors return plain text."""
        assert colors_disabled.error("error") == "error"
        assert colors_disabled.success("success") == "success"
        assert colors_disabled.muted("muted") == "muted"
        assert colors_disabled.info("info") == "info"

    def test_import_combined_success_format(self, colors: Colors) -> None:
        """Verify combined success + info format for 'Saved to <path>' message."""
        dest = "/home/user/.tmuxp/session.yaml"
        output = colors.success("Saved to ") + colors.info(dest) + "."
        # Should contain both green and cyan ANSI codes
        assert "\033[32m" in output  # green for "Saved to"
        assert "\033[36m" in output  # cyan for path
        assert "Saved to" in output
        assert dest in output
        assert output.endswith(".")

    def test_import_help_text_with_urls(self, colors: Colors) -> None:
        """Verify help text uses muted for text and info for URLs."""
        url = "<http://tmuxp.git-pull.com/examples.html>"
        help_text = colors.muted(
            "tmuxp has examples in JSON and YAML format at "
        ) + colors.info(url)
        assert "\033[34m" in help_text  # blue for muted text
        assert "\033[36m" in help_text  # cyan for URL
        assert url in help_text

    def test_import_banner_with_separator(self, colors: Colors) -> None:
        """Verify banner format with separator and instruction text."""
        config_content = "session_name: test\n"
        separator = "---------------------------------------------------------------"
        output = (
            config_content
            + colors.muted(separator)
            + "\n"
            + colors.muted("Configuration import does its best to convert files.")
            + "\n"
        )
        # Should contain blue ANSI code for muted sections
        assert "\033[34m" in output
        assert separator in output
        assert "Configuration import" in output
        assert config_content in output
