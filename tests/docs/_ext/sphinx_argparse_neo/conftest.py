"""Fixtures and configuration for sphinx_argparse_neo tests."""

from __future__ import annotations

import argparse
import pathlib
import sys

import pytest

# Add docs/_ext to path so we can import the extension module
docs_ext_path = (
    pathlib.Path(__file__).parent.parent.parent.parent.parent / "docs" / "_ext"
)
if str(docs_ext_path) not in sys.path:
    sys.path.insert(0, str(docs_ext_path))


@pytest.fixture
def simple_parser() -> argparse.ArgumentParser:
    """Create a simple parser with basic arguments.

    Returns
    -------
    argparse.ArgumentParser
        Parser with a positional argument and a couple of options.
    """
    parser = argparse.ArgumentParser(
        prog="myapp",
        description="A simple test application",
    )
    parser.add_argument("filename", help="Input file to process")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose mode"
    )
    parser.add_argument("-o", "--output", metavar="FILE", help="Output file")
    return parser


@pytest.fixture
def parser_with_groups() -> argparse.ArgumentParser:
    """Create a parser with custom argument groups.

    Returns
    -------
    argparse.ArgumentParser
        Parser with multiple argument groups.
    """
    parser = argparse.ArgumentParser(prog="grouped", description="Parser with groups")

    input_group = parser.add_argument_group("Input Options", "Options for input")
    input_group.add_argument("--input", "-i", required=True, help="Input file")
    input_group.add_argument("--format", choices=["json", "yaml"], help="Input format")

    output_group = parser.add_argument_group("Output Options", "Options for output")
    output_group.add_argument("--output", "-o", help="Output file")
    output_group.add_argument("--pretty", action="store_true", help="Pretty print")

    return parser


@pytest.fixture
def parser_with_subcommands() -> argparse.ArgumentParser:
    """Create a parser with subcommands.

    Returns
    -------
    argparse.ArgumentParser
        Parser with subparsers.
    """
    parser = argparse.ArgumentParser(prog="cli", description="CLI with subcommands")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Sync subcommand
    sync_parser = subparsers.add_parser("sync", help="Synchronize repositories")
    sync_parser.add_argument("repo", nargs="?", help="Repository to sync")
    sync_parser.add_argument("-f", "--force", action="store_true", help="Force sync")

    # Add subcommand
    add_parser = subparsers.add_parser("add", aliases=["a"], help="Add a repository")
    add_parser.add_argument("url", help="Repository URL")
    add_parser.add_argument("-n", "--name", help="Repository name")

    return parser


@pytest.fixture
def parser_with_mutex() -> argparse.ArgumentParser:
    """Create a parser with mutually exclusive arguments.

    Returns
    -------
    argparse.ArgumentParser
        Parser with mutually exclusive group.
    """
    parser = argparse.ArgumentParser(prog="mutex", description="Parser with mutex")

    mutex = parser.add_mutually_exclusive_group(required=True)
    mutex.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    mutex.add_argument("-q", "--quiet", action="store_true", help="Quiet output")

    return parser


@pytest.fixture
def parser_with_all_actions() -> argparse.ArgumentParser:
    """Create a parser with all action types.

    Returns
    -------
    argparse.ArgumentParser
        Parser demonstrating all action types.
    """
    parser = argparse.ArgumentParser(prog="actions", description="All action types")

    # store (default)
    parser.add_argument("--name", help="Store action")

    # store_const
    parser.add_argument(
        "--enable", action="store_const", const="enabled", help="Store const"
    )

    # store_true / store_false
    parser.add_argument("--flag", action="store_true", help="Store true")
    parser.add_argument("--no-flag", action="store_false", help="Store false")

    # append
    parser.add_argument("--item", action="append", help="Append action")

    # append_const
    parser.add_argument(
        "--debug",
        action="append_const",
        const="debug",
        dest="features",
        help="Append const",
    )

    # count
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Count")

    # BooleanOptionalAction (Python 3.9+)
    parser.add_argument(
        "--option", action=argparse.BooleanOptionalAction, help="Boolean optional"
    )

    return parser


@pytest.fixture
def parser_with_types() -> argparse.ArgumentParser:
    """Create a parser with typed arguments.

    Returns
    -------
    argparse.ArgumentParser
        Parser with various type specifications.
    """
    parser = argparse.ArgumentParser(prog="types", description="Typed arguments")

    parser.add_argument("--count", type=int, help="Integer argument")
    parser.add_argument("--ratio", type=float, help="Float argument")
    parser.add_argument("--path", type=pathlib.Path, help="Path argument")
    parser.add_argument("--choice", type=str, choices=["a", "b", "c"], help="Choices")

    return parser


@pytest.fixture
def parser_with_nargs() -> argparse.ArgumentParser:
    """Create a parser demonstrating nargs variants.

    Returns
    -------
    argparse.ArgumentParser
        Parser with various nargs specifications.
    """
    parser = argparse.ArgumentParser(prog="nargs", description="Nargs variants")

    parser.add_argument("single", help="Single positional")
    parser.add_argument("optional", nargs="?", default="default", help="Optional")
    parser.add_argument("zero_or_more", nargs="*", help="Zero or more")
    parser.add_argument("--one-or-more", nargs="+", help="One or more")
    parser.add_argument("--exactly-two", nargs=2, metavar=("A", "B"), help="Exactly 2")
    parser.add_argument("remainder", nargs=argparse.REMAINDER, help="Remainder")

    return parser


@pytest.fixture
def parser_with_defaults() -> argparse.ArgumentParser:
    """Create a parser with various default values.

    Returns
    -------
    argparse.ArgumentParser
        Parser demonstrating default handling.
    """
    parser = argparse.ArgumentParser(prog="defaults")

    parser.add_argument("--none-default", default=None, help="None default")
    parser.add_argument("--string-default", default="hello", help="String default")
    parser.add_argument("--int-default", default=42, type=int, help="Int default")
    parser.add_argument("--list-default", default=[1, 2], help="List default")
    parser.add_argument("--suppress", default=argparse.SUPPRESS, help=argparse.SUPPRESS)

    return parser


@pytest.fixture
def nested_subcommands_parser() -> argparse.ArgumentParser:
    """Create a parser with nested subcommands.

    Returns
    -------
    argparse.ArgumentParser
        Parser with multiple levels of subparsers.
    """
    parser = argparse.ArgumentParser(prog="nested", description="Nested subcommands")

    level1 = parser.add_subparsers(dest="level1")

    # First level: repo
    repo = level1.add_parser("repo", help="Repository commands")
    repo_subs = repo.add_subparsers(dest="level2")

    # Second level: repo clone
    clone = repo_subs.add_parser("clone", help="Clone a repository")
    clone.add_argument("url", help="Repository URL")

    # Second level: repo list
    repo_subs.add_parser("list", help="List repositories")

    return parser
