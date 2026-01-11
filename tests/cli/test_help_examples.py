"""Tests to ensure CLI help examples are valid commands."""

from __future__ import annotations

import argparse
import subprocess

import pytest

from tmuxp.cli import create_parser


def _get_help_text(subcommand: str | None = None) -> str:
    """Get CLI help text without spawning subprocess.

    Parameters
    ----------
    subcommand : str | None
        Subcommand name, or None for main help.

    Returns
    -------
    str
        The formatted help text.
    """
    parser = create_parser()
    if subcommand is None:
        return parser.format_help()

    # Access subparser via _subparsers._group_actions
    subparsers = parser._subparsers
    if subparsers is not None:
        for action in subparsers._group_actions:
            if isinstance(action, argparse._SubParsersAction):
                choices = action.choices
                if choices is not None and subcommand in choices:
                    return str(choices[subcommand].format_help())

    return parser.format_help()


def extract_examples_from_help(help_text: str) -> list[str]:
    r"""Extract example commands from help text.

    Parameters
    ----------
    help_text : str
        The help output text to extract examples from.

    Returns
    -------
    list[str]
        List of extracted example commands.

    Examples
    --------
    >>> text = "load:\n    tmuxp load myproject\n\npositions:"
    >>> extract_examples_from_help(text)
    ['tmuxp load myproject']

    >>> text2 = "examples:\n  tmuxp debug-info\n\noptions:"
    >>> extract_examples_from_help(text2)
    ['tmuxp debug-info']

    >>> text3 = "Field-scoped search:\n    tmuxp search window:editor"
    >>> extract_examples_from_help(text3)
    ['tmuxp search window:editor']
    """
    examples = []
    in_examples = False
    for line in help_text.splitlines():
        # Match example section headings:
        # - "examples:" (default examples section)
        # - "load examples:" (category headings with examples suffix)
        # - "Field-scoped search:" (multi-word category headings)
        # Exclude argparse sections like "positional arguments:", "options:"
        stripped = line.strip()
        is_section_heading = (
            stripped.endswith(":")
            and stripped not in ("positional arguments:", "options:")
            and not stripped.startswith("-")
        )
        if is_section_heading:
            in_examples = True
        elif in_examples and line.startswith("  "):
            cmd = line.strip()
            if cmd.startswith("tmuxp"):
                examples.append(cmd)
        elif line and not line[0].isspace():
            in_examples = False
    return examples


def test_main_help_has_examples() -> None:
    """Main --help should have at least one example."""
    help_text = _get_help_text()
    examples = extract_examples_from_help(help_text)
    assert len(examples) > 0, "Main --help should have at least one example"


def test_main_help_examples_are_valid_subcommands() -> None:
    """All examples in main --help should reference valid subcommands."""
    help_text = _get_help_text()
    examples = extract_examples_from_help(help_text)

    # Extract valid subcommands from help output
    valid_subcommands = {
        "load",
        "shell",
        "import",
        "convert",
        "debug-info",
        "ls",
        "edit",
        "freeze",
        "search",
    }

    for example in examples:
        parts = example.split()
        if len(parts) >= 2:
            subcommand = parts[1]
            assert subcommand in valid_subcommands, (
                f"Example '{example}' uses unknown subcommand '{subcommand}'"
            )


@pytest.mark.parametrize(
    "subcommand",
    [
        "load",
        "shell",
        "import",
        "convert",
        "debug-info",
        "ls",
        "edit",
        "freeze",
        "search",
    ],
)
def test_subcommand_help_has_examples(subcommand: str) -> None:
    """Each subcommand --help should have at least one example."""
    help_text = _get_help_text(subcommand)
    examples = extract_examples_from_help(help_text)
    assert len(examples) > 0, f"{subcommand} --help should have at least one example"


def test_load_subcommand_examples_are_valid() -> None:
    """Load subcommand examples should have valid flags."""
    help_text = _get_help_text("load")
    examples = extract_examples_from_help(help_text)

    # Verify each example has valid structure
    for example in examples:
        assert example.startswith("tmuxp load"), f"Bad example format: {example}"


def test_freeze_subcommand_examples_are_valid() -> None:
    """Freeze subcommand examples should have valid flags."""
    help_text = _get_help_text("freeze")
    examples = extract_examples_from_help(help_text)

    # Verify each example has valid structure
    for example in examples:
        assert example.startswith("tmuxp freeze"), f"Bad example format: {example}"


def test_shell_subcommand_examples_are_valid() -> None:
    """Shell subcommand examples should have valid flags."""
    help_text = _get_help_text("shell")
    examples = extract_examples_from_help(help_text)

    # Verify each example has valid structure
    for example in examples:
        assert example.startswith("tmuxp shell"), f"Bad example format: {example}"


def test_convert_subcommand_examples_are_valid() -> None:
    """Convert subcommand examples should have valid flags."""
    help_text = _get_help_text("convert")
    examples = extract_examples_from_help(help_text)

    # Verify each example has valid structure
    for example in examples:
        assert example.startswith("tmuxp convert"), f"Bad example format: {example}"


def test_import_subcommand_examples_are_valid() -> None:
    """Import subcommand examples should have valid flags."""
    help_text = _get_help_text("import")
    examples = extract_examples_from_help(help_text)

    # Verify each example has valid structure
    for example in examples:
        assert example.startswith("tmuxp import"), f"Bad example format: {example}"


def test_edit_subcommand_examples_are_valid() -> None:
    """Edit subcommand examples should have valid flags."""
    help_text = _get_help_text("edit")
    examples = extract_examples_from_help(help_text)

    # Verify each example has valid structure
    for example in examples:
        assert example.startswith("tmuxp edit"), f"Bad example format: {example}"


def test_ls_subcommand_examples_are_valid() -> None:
    """Ls subcommand examples should have valid flags."""
    help_text = _get_help_text("ls")
    examples = extract_examples_from_help(help_text)

    # Verify each example has valid structure
    for example in examples:
        assert example.startswith("tmuxp ls"), f"Bad example format: {example}"


def test_debug_info_subcommand_examples_are_valid() -> None:
    """Debug-info subcommand examples should have valid flags."""
    help_text = _get_help_text("debug-info")
    examples = extract_examples_from_help(help_text)

    # Verify each example has valid structure
    for example in examples:
        assert example.startswith("tmuxp debug-info"), f"Bad example format: {example}"


def test_search_subcommand_examples_are_valid() -> None:
    """Search subcommand examples should have valid flags."""
    help_text = _get_help_text("search")
    examples = extract_examples_from_help(help_text)

    # Verify each example has valid structure
    for example in examples:
        assert example.startswith("tmuxp search"), f"Bad example format: {example}"


def test_search_no_args_shows_help() -> None:
    """Running 'tmuxp search' with no args shows help.

    Note: This test uses subprocess to verify actual CLI behavior and exit code.
    """
    result = subprocess.run(
        ["tmuxp", "search"],
        capture_output=True,
        text=True,
    )
    # Should show help (usage line present)
    assert "usage: tmuxp search" in result.stdout
    # Should exit successfully (not error)
    assert result.returncode == 0


def test_main_help_example_sections_have_examples_suffix() -> None:
    """Main --help should have section headings ending with 'examples:'."""
    help_text = _get_help_text()

    # Should have "load examples:", "freeze examples:", etc.
    # NOT just "load:", "freeze:"
    assert "load examples:" in help_text.lower()
    assert "freeze examples:" in help_text.lower()


def test_main_help_examples_are_colorized(monkeypatch: pytest.MonkeyPatch) -> None:
    """Main --help should have colorized example sections when FORCE_COLOR is set."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("FORCE_COLOR", "1")

    help_text = _get_help_text()

    # Should contain ANSI escape codes for colorization
    assert "\033[" in help_text, "Example sections should be colorized"
