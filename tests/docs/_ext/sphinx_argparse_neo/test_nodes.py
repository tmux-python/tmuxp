"""Tests for sphinx_argparse_neo.nodes module."""

from __future__ import annotations

from docutils import nodes
from sphinx_argparse_neo.nodes import (
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
