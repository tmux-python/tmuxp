"""Tests for colored prompt utilities."""

from __future__ import annotations

import pathlib

import pytest

from tests.cli.conftest import ANSI_BLUE, ANSI_CYAN, ANSI_RESET
from tmuxp.cli._colors import ColorMode, Colors


def test_prompt_bool_choice_indicator_muted(colors_always: Colors) -> None:
    """Verify [Y/n] uses muted color (blue)."""
    # Test the muted color is applied to choice indicators
    result = colors_always.muted("[Y/n]")
    assert ANSI_BLUE in result  # blue foreground
    assert "[Y/n]" in result
    assert result.endswith(ANSI_RESET)


def test_prompt_bool_choice_indicator_variants(colors_always: Colors) -> None:
    """Verify all choice indicator variants are colored."""
    for indicator in ["[Y/n]", "[y/N]", "[y/n]"]:
        result = colors_always.muted(indicator)
        assert ANSI_BLUE in result
        assert indicator in result


def test_prompt_default_value_uses_info(colors_always: Colors) -> None:
    """Verify default path uses info color (cyan)."""
    path = "/home/user/.tmuxp/session.yaml"
    result = colors_always.info(f"[{path}]")
    assert ANSI_CYAN in result  # cyan foreground
    assert path in result
    assert result.endswith(ANSI_RESET)


def test_prompt_choices_list_muted(colors_always: Colors) -> None:
    """Verify (yaml, json) uses muted color (blue)."""
    choices = "(yaml, json)"
    result = colors_always.muted(choices)
    assert ANSI_BLUE in result  # blue foreground
    assert choices in result


def test_prompts_respect_no_color_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify NO_COLOR disables prompt colors."""
    monkeypatch.setenv("NO_COLOR", "1")
    colors = Colors(ColorMode.AUTO)

    assert colors.muted("[Y/n]") == "[Y/n]"
    assert colors.info("[default]") == "[default]"


def test_prompt_combined_format(colors_always: Colors) -> None:
    """Verify combined prompt format with choices and default."""
    name = "Convert to"
    choices_str = colors_always.muted("(yaml, json)")
    default_str = colors_always.info("[yaml]")
    prompt = f"{name} - {choices_str} {default_str}"

    # Should contain both blue (muted) and cyan (info) ANSI codes
    assert ANSI_BLUE in prompt  # blue for choices
    assert ANSI_CYAN in prompt  # cyan for default
    assert "Convert to" in prompt
    assert "yaml, json" in prompt


def test_prompt_colors_disabled_returns_plain_text(colors_never: Colors) -> None:
    """Verify disabled colors return plain text without ANSI codes."""
    assert colors_never.muted("[Y/n]") == "[Y/n]"
    assert colors_never.info("[/path/to/file]") == "[/path/to/file]"
    assert "\033[" not in colors_never.muted("test")
    assert "\033[" not in colors_never.info("test")


def test_prompt_empty_input_no_default_reprompts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify prompt() re-prompts when user enters empty input with no default.

    This is a regression test for the bug where pressing Enter with no default
    would cause an AssertionError instead of re-prompting.
    """
    from tmuxp.cli.utils import prompt

    # Simulate: first input is empty (user presses Enter), second input is valid
    inputs = iter(["", "valid_input"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    result = prompt("Enter value")
    assert result == "valid_input"


def test_prompt_empty_input_with_value_proc_no_crash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify prompt() with value_proc doesn't crash on empty input.

    This is a regression test for the AssertionError that occurred when
    value_proc was provided but input was empty and no default was set.
    """
    from tmuxp.cli.utils import prompt

    def validate_path(val: str) -> str:
        """Validate that path is absolute."""
        if not val.startswith("/"):
            msg = "Must be absolute path"
            raise ValueError(msg)
        return val

    # Simulate: first input is empty, second input is valid
    inputs = iter(["", "/valid/path"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    result = prompt("Enter path", value_proc=validate_path)
    assert result == "/valid/path"


def test_prompt_default_uses_private_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
) -> None:
    """Verify prompt() masks home directory in default value display.

    The displayed default should use PrivatePath to show ~ instead of
    the full home directory path.
    """
    import pathlib

    from tmuxp.cli.utils import prompt

    # Create a path under the user's home directory
    home = pathlib.Path.home()
    test_path = str(home / ".tmuxp" / "session.yaml")

    # Capture what prompt displays
    displayed_prompt = None

    def capture_input(prompt_text: str) -> str:
        nonlocal displayed_prompt
        displayed_prompt = prompt_text
        return ""  # User presses Enter, accepting default

    monkeypatch.setattr("builtins.input", capture_input)

    result = prompt("Save to", default=test_path)

    # The result should be the original path (for actual saving)
    assert result == test_path

    # The displayed prompt should use ~ instead of full home path
    assert displayed_prompt is not None
    assert "~/.tmuxp/session.yaml" in displayed_prompt
    assert str(home) not in displayed_prompt
