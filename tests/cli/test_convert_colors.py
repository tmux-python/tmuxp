"""Tests for CLI colors in convert command."""

from __future__ import annotations

import pytest

from tmuxp.cli._colors import ColorMode, Colors


class TestConvertColorOutput:
    """Tests for convert command color output formatting."""

    @pytest.fixture()
    def colors(self, monkeypatch: pytest.MonkeyPatch) -> Colors:
        """Create a Colors instance with colors enabled."""
        monkeypatch.delenv("NO_COLOR", raising=False)
        return Colors(ColorMode.ALWAYS)

    @pytest.fixture()
    def colors_disabled(self) -> Colors:
        """Create a Colors instance with colors disabled."""
        return Colors(ColorMode.NEVER)

    def test_convert_success_message(self, colors: Colors) -> None:
        """Verify success messages use success color (green)."""
        result = colors.success("New workspace file saved to ")
        assert "\033[32m" in result  # green foreground
        assert "New workspace file saved to" in result

    def test_convert_file_path_uses_info(self, colors: Colors) -> None:
        """Verify file paths use info color (cyan)."""
        path = "/path/to/config.yaml"
        result = colors.info(path)
        assert "\033[36m" in result  # cyan foreground
        assert path in result

    def test_convert_format_type_highlighted(self, colors: Colors) -> None:
        """Verify format type uses highlight color (magenta + bold)."""
        for fmt in ["json", "yaml"]:
            result = colors.highlight(fmt)
            assert "\033[35m" in result  # magenta foreground
            assert "\033[1m" in result  # bold
            assert fmt in result

    def test_convert_colors_disabled_plain_text(self, colors_disabled: Colors) -> None:
        """Verify disabled colors return plain text."""
        assert colors_disabled.success("success") == "success"
        assert colors_disabled.info("info") == "info"
        assert colors_disabled.highlight("highlight") == "highlight"

    def test_convert_combined_success_format(self, colors: Colors) -> None:
        """Verify combined success + info format for save message."""
        newfile = "/home/user/.tmuxp/session.json"
        output = (
            colors.success("New workspace file saved to ")
            + colors.info(f"<{newfile}>")
            + "."
        )
        # Should contain both green and cyan ANSI codes
        assert "\033[32m" in output  # green for success text
        assert "\033[36m" in output  # cyan for path
        assert "New workspace file saved to" in output
        assert newfile in output
        assert output.endswith(".")

    def test_convert_prompt_format_with_highlight(self, colors: Colors) -> None:
        """Verify prompt uses info for path and highlight for format."""
        workspace_file = "/path/to/config.yaml"
        to_filetype = "json"
        prompt = (
            f"Convert {colors.info(workspace_file)} to {colors.highlight(to_filetype)}?"
        )
        assert "\033[36m" in prompt  # cyan for file path
        assert "\033[35m" in prompt  # magenta for format type
        assert workspace_file in prompt
        assert to_filetype in prompt

    def test_convert_save_prompt_format(self, colors: Colors) -> None:
        """Verify save prompt uses info color for new file path."""
        newfile = "/path/to/config.json"
        prompt = f"Save workspace to {colors.info(newfile)}?"
        assert "\033[36m" in prompt  # cyan for file path
        assert newfile in prompt
        assert "Save workspace to" in prompt
