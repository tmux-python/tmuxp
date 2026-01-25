"""Tests for sphinx_argparse_neo.nodes module."""

from __future__ import annotations

import re
import typing as t

import pytest
from docutils import nodes
from sphinx_argparse_neo.nodes import (
    _generate_argument_id,
    argparse_argument,
    argparse_group,
    argparse_program,
    argparse_subcommand,
    argparse_subcommands,
    argparse_usage,
)

# --- Node creation tests ---


def test_argparse_program_creation() -> None:
    """Test creating argparse_program node."""
    node = argparse_program()
    node["prog"] = "myapp"

    assert node["prog"] == "myapp"
    assert isinstance(node, nodes.General)
    assert isinstance(node, nodes.Element)


def test_argparse_usage_creation() -> None:
    """Test creating argparse_usage node."""
    node = argparse_usage()
    node["usage"] = "myapp [-h] [--verbose] command"

    assert node["usage"] == "myapp [-h] [--verbose] command"


def test_argparse_group_creation() -> None:
    """Test creating argparse_group node."""
    node = argparse_group()
    node["title"] = "Output Options"
    node["description"] = "Control output format"

    assert node["title"] == "Output Options"
    assert node["description"] == "Control output format"


def test_argparse_argument_creation() -> None:
    """Test creating argparse_argument node."""
    node = argparse_argument()
    node["names"] = ["-v", "--verbose"]
    node["help"] = "Enable verbose mode"
    node["metavar"] = None
    node["required"] = False

    assert node["names"] == ["-v", "--verbose"]
    assert node["help"] == "Enable verbose mode"


def test_argparse_subcommands_creation() -> None:
    """Test creating argparse_subcommands node."""
    node = argparse_subcommands()
    node["title"] = "Commands"

    assert node["title"] == "Commands"


def test_argparse_subcommand_creation() -> None:
    """Test creating argparse_subcommand node."""
    node = argparse_subcommand()
    node["name"] = "sync"
    node["aliases"] = ["s"]
    node["help"] = "Synchronize repositories"

    assert node["name"] == "sync"
    assert node["aliases"] == ["s"]


# --- Node nesting tests ---


def test_program_can_contain_usage() -> None:
    """Test that program node can contain usage node."""
    program = argparse_program()
    program["prog"] = "myapp"

    usage = argparse_usage()
    usage["usage"] = "myapp [-h]"

    program.append(usage)

    assert len(program.children) == 1
    assert isinstance(program.children[0], argparse_usage)


def test_program_can_contain_groups() -> None:
    """Test that program node can contain group nodes."""
    program = argparse_program()

    group1 = argparse_group()
    group1["title"] = "Positional Arguments"

    group2 = argparse_group()
    group2["title"] = "Optional Arguments"

    program.append(group1)
    program.append(group2)

    assert len(program.children) == 2


def test_group_can_contain_arguments() -> None:
    """Test that group node can contain argument nodes."""
    group = argparse_group()
    group["title"] = "Options"

    arg1 = argparse_argument()
    arg1["names"] = ["-v"]

    arg2 = argparse_argument()
    arg2["names"] = ["-o"]

    group.append(arg1)
    group.append(arg2)

    assert len(group.children) == 2


def test_subcommands_can_contain_subcommand() -> None:
    """Test that subcommands container can contain subcommand nodes."""
    container = argparse_subcommands()
    container["title"] = "Commands"

    sub1 = argparse_subcommand()
    sub1["name"] = "sync"

    sub2 = argparse_subcommand()
    sub2["name"] = "add"

    container.append(sub1)
    container.append(sub2)

    assert len(container.children) == 2


def test_subcommand_can_contain_program() -> None:
    """Test that subcommand can contain nested program (for recursion)."""
    subcommand = argparse_subcommand()
    subcommand["name"] = "sync"

    nested_program = argparse_program()
    nested_program["prog"] = "myapp sync"

    subcommand.append(nested_program)

    assert len(subcommand.children) == 1
    assert isinstance(subcommand.children[0], argparse_program)


# --- Attribute handling tests ---


def test_argument_with_all_attributes() -> None:
    """Test argument node with all possible attributes."""
    node = argparse_argument()
    node["names"] = ["-f", "--file"]
    node["help"] = "Input file"
    node["metavar"] = "FILE"
    node["required"] = True
    node["default_string"] = "input.txt"
    node["choices"] = ["a", "b", "c"]
    node["type_name"] = "str"
    node["mutex"] = False
    node["mutex_required"] = False

    assert node["names"] == ["-f", "--file"]
    assert node["help"] == "Input file"
    assert node["metavar"] == "FILE"
    assert node["required"] is True
    assert node["default_string"] == "input.txt"
    assert node["choices"] == ["a", "b", "c"]
    assert node["type_name"] == "str"


def test_argument_with_mutex_marker() -> None:
    """Test argument node marked as part of mutex group."""
    node = argparse_argument()
    node["names"] = ["-v"]
    node["mutex"] = True
    node["mutex_required"] = True

    assert node["mutex"] is True
    assert node["mutex_required"] is True


def test_node_get_with_default() -> None:
    """Test getting attributes with defaults."""
    node = argparse_argument()
    node["names"] = ["-v"]

    # Attribute that exists
    assert node.get("names") == ["-v"]

    # Attribute that doesn't exist - get() returns None
    assert node.get("nonexistent") is None

    # Attribute with explicit default
    assert node.get("help", "default help") == "default help"


# --- Full tree construction test ---


def test_full_node_tree() -> None:
    """Test constructing a complete node tree."""
    # Root program
    program = argparse_program()
    program["prog"] = "myapp"

    # Usage
    usage = argparse_usage()
    usage["usage"] = "myapp [-h] [-v] command"
    program.append(usage)

    # Positional group
    pos_group = argparse_group()
    pos_group["title"] = "Positional Arguments"

    cmd_arg = argparse_argument()
    cmd_arg["names"] = ["command"]
    cmd_arg["help"] = "Command to run"
    pos_group.append(cmd_arg)
    program.append(pos_group)

    # Optional group
    opt_group = argparse_group()
    opt_group["title"] = "Optional Arguments"

    verbose = argparse_argument()
    verbose["names"] = ["-v", "--verbose"]
    verbose["help"] = "Verbose mode"
    opt_group.append(verbose)
    program.append(opt_group)

    # Subcommands
    subs = argparse_subcommands()
    subs["title"] = "Commands"

    sync_sub = argparse_subcommand()
    sync_sub["name"] = "sync"
    sync_sub["help"] = "Sync repos"
    subs.append(sync_sub)

    program.append(subs)

    # Verify tree structure
    assert len(program.children) == 4  # usage, pos_group, opt_group, subs
    assert isinstance(program.children[0], argparse_usage)
    assert isinstance(program.children[1], argparse_group)
    assert isinstance(program.children[2], argparse_group)
    assert isinstance(program.children[3], argparse_subcommands)


# --- ID generation tests ---


def test_generate_argument_id_short_option() -> None:
    """Test ID generation for short option."""
    assert _generate_argument_id(["-L"]) == "L"


def test_generate_argument_id_long_option() -> None:
    """Test ID generation for long option."""
    assert _generate_argument_id(["--help"]) == "help"


def test_generate_argument_id_multiple_names() -> None:
    """Test ID generation for argument with multiple names."""
    assert _generate_argument_id(["-v", "--verbose"]) == "v-verbose"


def test_generate_argument_id_with_prefix() -> None:
    """Test ID generation with prefix for namespace isolation."""
    assert _generate_argument_id(["-L"], "shell") == "shell-L"
    assert _generate_argument_id(["--help"], "load") == "load-help"


def test_generate_argument_id_positional() -> None:
    """Test ID generation for positional argument."""
    assert _generate_argument_id(["filename"]) == "filename"


def test_generate_argument_id_empty() -> None:
    """Test ID generation with empty names list."""
    assert _generate_argument_id([]) == ""


def test_generate_argument_id_prefix_no_names() -> None:
    """Test that prefix alone doesn't create ID when no names."""
    assert _generate_argument_id([], "shell") == ""


# --- HTML rendering tests using NamedTuple for parametrization ---


class ArgumentHTMLCase(t.NamedTuple):
    """Test case for argument HTML rendering."""

    test_id: str
    names: list[str]
    metavar: str | None
    help_text: str | None
    default: str | None
    id_prefix: str
    expected_patterns: list[str]  # Regex patterns to match


ARGUMENT_HTML_CASES = [
    ArgumentHTMLCase(
        test_id="short_option_with_metavar",
        names=["-L"],
        metavar="socket-name",
        help_text="pass-through for tmux -L",
        default="None",
        id_prefix="shell",
        expected_patterns=[
            r'<div class="argparse-argument-wrapper" id="shell-L">',
            r'<dt class="argparse-argument-name">',
            r'<span class="na">-L</span>',
            r'<span class="nv">socket-name</span>',
            r'<a class="headerlink" href="#shell-L">¶</a>',
            r'Default: <span class="nv">None</span>',
            r"</div>",
        ],
    ),
    ArgumentHTMLCase(
        test_id="long_option",
        names=["--help"],
        metavar=None,
        help_text="show help",
        default=None,
        id_prefix="",
        expected_patterns=[
            r'<span class="nt">--help</span>',
            r'id="help"',
            r'href="#help"',
        ],
    ),
    ArgumentHTMLCase(
        test_id="positional_argument",
        names=["filename"],
        metavar=None,
        help_text="input file",
        default=None,
        id_prefix="",
        expected_patterns=[
            r'<span class="nl">filename</span>',
            r'id="filename"',
        ],
    ),
    ArgumentHTMLCase(
        test_id="multiple_names",
        names=["-v", "--verbose"],
        metavar=None,
        help_text="Enable verbose mode",
        default=None,
        id_prefix="load",
        expected_patterns=[
            r'id="load-v-verbose"',
            r'<span class="na">-v</span>',
            r'<span class="nt">--verbose</span>',
            r'href="#load-v-verbose"',
        ],
    ),
]


class MockTranslator:
    """Mock HTML5Translator for testing HTML generation."""

    def __init__(self) -> None:
        """Initialize mock translator."""
        self.body: list[str] = []

    def encode(self, text: str) -> str:
        """HTML encode text."""
        return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_argument_to_html(
    names: list[str],
    metavar: str | None,
    help_text: str | None,
    default: str | None,
    id_prefix: str,
) -> str:
    """Render an argument node to HTML string for testing.

    Parameters
    ----------
    names
        Argument names (e.g., ["-v", "--verbose"]).
    metavar
        Optional metavar (e.g., "FILE").
    help_text
        Help text for the argument.
    default
        Default value string.
    id_prefix
        Prefix for the argument ID.

    Returns
    -------
    str
        HTML string from the mock translator's body.
    """
    from sphinx_argparse_neo.nodes import (
        depart_argparse_argument_html,
        visit_argparse_argument_html,
    )

    node = argparse_argument()
    node["names"] = names
    node["metavar"] = metavar
    node["help"] = help_text
    node["default_string"] = default
    node["id_prefix"] = id_prefix

    translator = MockTranslator()
    visit_argparse_argument_html(translator, node)
    depart_argparse_argument_html(translator, node)

    return "".join(translator.body)


@pytest.mark.parametrize(
    "case",
    ARGUMENT_HTML_CASES,
    ids=lambda c: c.test_id,
)
def test_argument_html_rendering(case: ArgumentHTMLCase) -> None:
    """Test HTML output for argument nodes."""
    html = render_argument_to_html(
        names=case.names,
        metavar=case.metavar,
        help_text=case.help_text,
        default=case.default,
        id_prefix=case.id_prefix,
    )

    for pattern in case.expected_patterns:
        assert re.search(pattern, html), f"Pattern not found: {pattern}\nHTML: {html}"


def test_argument_wrapper_has_id() -> None:
    """Verify wrapper div has correct ID attribute."""
    html = render_argument_to_html(
        names=["-f", "--file"],
        metavar="PATH",
        help_text="Input file",
        default=None,
        id_prefix="convert",
    )

    assert 'id="convert-f-file"' in html
    assert '<div class="argparse-argument-wrapper"' in html


def test_argument_headerlink_present() -> None:
    """Verify headerlink anchor exists with correct href."""
    html = render_argument_to_html(
        names=["--output"],
        metavar="FILE",
        help_text="Output file",
        default=None,
        id_prefix="freeze",
    )

    assert '<a class="headerlink" href="#freeze-output">¶</a>' in html


def test_default_value_styled() -> None:
    """Verify default value is wrapped in nv span."""
    html = render_argument_to_html(
        names=["--format"],
        metavar=None,
        help_text="Output format",
        default="json",
        id_prefix="",
    )

    assert 'Default: <span class="nv">json</span>' in html


def test_wrapper_div_closed() -> None:
    """Verify wrapper div is properly closed."""
    html = render_argument_to_html(
        names=["-v"],
        metavar=None,
        help_text="Verbose",
        default=None,
        id_prefix="",
    )

    # Count opening and closing div tags
    open_divs = html.count("<div")
    close_divs = html.count("</div>")
    assert open_divs == close_divs, f"Unbalanced divs in HTML: {html}"


def test_argument_no_id_prefix() -> None:
    """Test argument rendering without ID prefix."""
    html = render_argument_to_html(
        names=["--debug"],
        metavar=None,
        help_text="Enable debug mode",
        default=None,
        id_prefix="",
    )

    assert 'id="debug"' in html
    assert 'href="#debug"' in html
