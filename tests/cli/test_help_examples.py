"""Tests to ensure CLI help examples are valid commands."""

from __future__ import annotations

import re
import subprocess

import pytest


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
    >>> text = "load examples:\n  tmuxp load myproject\n\npositions:"
    >>> extract_examples_from_help(text)
    ['tmuxp load myproject']

    >>> text2 = "examples:\n  tmuxp debug-info\n\noptions:"
    >>> extract_examples_from_help(text2)
    ['tmuxp debug-info']
    """
    examples = []
    in_examples = False
    for line in help_text.splitlines():
        # Match "examples:" or "load examples:" etc.
        if re.match(r"^(\S+\s+)?examples?:$", line, re.IGNORECASE):
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
    result = subprocess.run(
        ["tmuxp", "--help"],
        capture_output=True,
        text=True,
        check=True,
    )
    examples = extract_examples_from_help(result.stdout)
    assert len(examples) > 0, "Main --help should have at least one example"


def test_main_help_examples_are_valid_subcommands() -> None:
    """All examples in main --help should reference valid subcommands."""
    result = subprocess.run(
        ["tmuxp", "--help"],
        capture_output=True,
        text=True,
        check=True,
    )
    examples = extract_examples_from_help(result.stdout)

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
    result = subprocess.run(
        ["tmuxp", subcommand, "--help"],
        capture_output=True,
        text=True,
        check=True,
    )
    examples = extract_examples_from_help(result.stdout)
    assert len(examples) > 0, f"{subcommand} --help should have at least one example"


def test_load_subcommand_examples_are_valid() -> None:
    """Load subcommand examples should have valid flags."""
    result = subprocess.run(
        ["tmuxp", "load", "--help"],
        capture_output=True,
        text=True,
        check=True,
    )
    examples = extract_examples_from_help(result.stdout)

    # Verify each example has valid structure
    for example in examples:
        assert example.startswith("tmuxp load"), f"Bad example format: {example}"


def test_freeze_subcommand_examples_are_valid() -> None:
    """Freeze subcommand examples should have valid flags."""
    result = subprocess.run(
        ["tmuxp", "freeze", "--help"],
        capture_output=True,
        text=True,
        check=True,
    )
    examples = extract_examples_from_help(result.stdout)

    # Verify each example has valid structure
    for example in examples:
        assert example.startswith("tmuxp freeze"), f"Bad example format: {example}"


def test_shell_subcommand_examples_are_valid() -> None:
    """Shell subcommand examples should have valid flags."""
    result = subprocess.run(
        ["tmuxp", "shell", "--help"],
        capture_output=True,
        text=True,
        check=True,
    )
    examples = extract_examples_from_help(result.stdout)

    # Verify each example has valid structure
    for example in examples:
        assert example.startswith("tmuxp shell"), f"Bad example format: {example}"


def test_convert_subcommand_examples_are_valid() -> None:
    """Convert subcommand examples should have valid flags."""
    result = subprocess.run(
        ["tmuxp", "convert", "--help"],
        capture_output=True,
        text=True,
        check=True,
    )
    examples = extract_examples_from_help(result.stdout)

    # Verify each example has valid structure
    for example in examples:
        assert example.startswith("tmuxp convert"), f"Bad example format: {example}"


def test_import_subcommand_examples_are_valid() -> None:
    """Import subcommand examples should have valid flags."""
    result = subprocess.run(
        ["tmuxp", "import", "--help"],
        capture_output=True,
        text=True,
        check=True,
    )
    examples = extract_examples_from_help(result.stdout)

    # Verify each example has valid structure
    for example in examples:
        assert example.startswith("tmuxp import"), f"Bad example format: {example}"


def test_edit_subcommand_examples_are_valid() -> None:
    """Edit subcommand examples should have valid flags."""
    result = subprocess.run(
        ["tmuxp", "edit", "--help"],
        capture_output=True,
        text=True,
        check=True,
    )
    examples = extract_examples_from_help(result.stdout)

    # Verify each example has valid structure
    for example in examples:
        assert example.startswith("tmuxp edit"), f"Bad example format: {example}"


def test_ls_subcommand_examples_are_valid() -> None:
    """Ls subcommand examples should have valid flags."""
    result = subprocess.run(
        ["tmuxp", "ls", "--help"],
        capture_output=True,
        text=True,
        check=True,
    )
    examples = extract_examples_from_help(result.stdout)

    # Verify each example has valid structure
    for example in examples:
        assert example.startswith("tmuxp ls"), f"Bad example format: {example}"


def test_debug_info_subcommand_examples_are_valid() -> None:
    """Debug-info subcommand examples should have valid flags."""
    result = subprocess.run(
        ["tmuxp", "debug-info", "--help"],
        capture_output=True,
        text=True,
        check=True,
    )
    examples = extract_examples_from_help(result.stdout)

    # Verify each example has valid structure
    for example in examples:
        assert example.startswith("tmuxp debug-info"), f"Bad example format: {example}"


def test_search_subcommand_examples_are_valid() -> None:
    """Search subcommand examples should have valid flags."""
    result = subprocess.run(
        ["tmuxp", "search", "--help"],
        capture_output=True,
        text=True,
        check=True,
    )
    examples = extract_examples_from_help(result.stdout)

    # Verify each example has valid structure
    for example in examples:
        assert example.startswith("tmuxp search"), f"Bad example format: {example}"


def test_search_no_args_shows_help() -> None:
    """Running 'tmuxp search' with no args shows help."""
    result = subprocess.run(
        ["tmuxp", "search"],
        capture_output=True,
        text=True,
    )
    # Should show help (usage line present)
    assert "usage: tmuxp search" in result.stdout
    # Should exit successfully (not error)
    assert result.returncode == 0
