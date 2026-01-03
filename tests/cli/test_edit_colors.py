"""Tests for CLI colors in edit command."""

from __future__ import annotations

import pytest

from tmuxp.cli._colors import ColorMode, Colors


class TestEditColorOutput:
    """Tests for edit command color output formatting."""

    @pytest.fixture()
    def colors(self, monkeypatch: pytest.MonkeyPatch) -> Colors:
        """Create a Colors instance with colors enabled."""
        monkeypatch.delenv("NO_COLOR", raising=False)
        return Colors(ColorMode.ALWAYS)

    @pytest.fixture()
    def colors_disabled(self) -> Colors:
        """Create a Colors instance with colors disabled."""
        return Colors(ColorMode.NEVER)

    def test_edit_opening_message_format(self, colors: Colors) -> None:
        """Verify opening message format with file path and editor."""
        workspace_file = "/home/user/.tmuxp/dev.yaml"
        editor = "vim"
        output = (
            colors.muted("Opening ")
            + colors.info(workspace_file)
            + colors.muted(" in ")
            + colors.highlight(editor, bold=False)
            + colors.muted("...")
        )
        # Should contain blue, cyan, and magenta ANSI codes
        assert "\033[34m" in output  # blue for muted
        assert "\033[36m" in output  # cyan for file path
        assert "\033[35m" in output  # magenta for editor
        assert workspace_file in output
        assert editor in output

    def test_edit_file_path_uses_info(self, colors: Colors) -> None:
        """Verify file paths use info color (cyan)."""
        path = "/path/to/workspace.yaml"
        result = colors.info(path)
        assert "\033[36m" in result  # cyan foreground
        assert path in result

    def test_edit_editor_highlighted(self, colors: Colors) -> None:
        """Verify editor name uses highlight color without bold."""
        for editor in ["vim", "nano", "code", "emacs", "nvim"]:
            result = colors.highlight(editor, bold=False)
            assert "\033[35m" in result  # magenta foreground
            assert "\033[1m" not in result  # no bold - subtle
            assert editor in result

    def test_edit_muted_for_static_text(self, colors: Colors) -> None:
        """Verify static text uses muted color (blue)."""
        result = colors.muted("Opening ")
        assert "\033[34m" in result  # blue foreground
        assert "Opening" in result

    def test_edit_colors_disabled_plain_text(self, colors_disabled: Colors) -> None:
        """Verify disabled colors return plain text."""
        workspace_file = "/home/user/.tmuxp/dev.yaml"
        editor = "vim"
        output = (
            colors_disabled.muted("Opening ")
            + colors_disabled.info(workspace_file)
            + colors_disabled.muted(" in ")
            + colors_disabled.highlight(editor, bold=False)
            + colors_disabled.muted("...")
        )
        # Should be plain text without ANSI codes
        assert "\033[" not in output
        assert output == f"Opening {workspace_file} in {editor}..."

    def test_edit_various_editors(self, colors: Colors) -> None:
        """Verify common editors can be highlighted."""
        editors = ["vim", "nvim", "nano", "code", "emacs", "hx", "micro"]
        for editor in editors:
            result = colors.highlight(editor, bold=False)
            assert "\033[35m" in result
            assert editor in result
