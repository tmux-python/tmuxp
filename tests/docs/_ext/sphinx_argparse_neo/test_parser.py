"""Tests for sphinx_argparse_neo.parser module."""

from __future__ import annotations

import argparse
import typing as t

import pytest
from sphinx_argparse_neo.parser import (
    ArgumentInfo,
    ParserInfo,
    SubcommandInfo,
    _extract_argument,
    _format_default,
    _get_action_name,
    _get_type_name,
    extract_parser,
)

# --- _format_default tests ---


class FormatDefaultFixture(t.NamedTuple):
    """Test fixture for _format_default function."""

    test_id: str
    default: t.Any
    expected: str | None


FORMAT_DEFAULT_FIXTURES: list[FormatDefaultFixture] = [
    FormatDefaultFixture(
        test_id="none_value",
        default=None,
        expected="None",
    ),
    FormatDefaultFixture(
        test_id="string_value",
        default="hello",
        expected="hello",
    ),
    FormatDefaultFixture(
        test_id="integer_value",
        default=42,
        expected="42",
    ),
    FormatDefaultFixture(
        test_id="float_value",
        default=3.14,
        expected="3.14",
    ),
    FormatDefaultFixture(
        test_id="list_value",
        default=[1, 2, 3],
        expected="[1, 2, 3]",
    ),
    FormatDefaultFixture(
        test_id="suppress_value",
        default=argparse.SUPPRESS,
        expected=None,
    ),
    FormatDefaultFixture(
        test_id="empty_string",
        default="",
        expected="",
    ),
    FormatDefaultFixture(
        test_id="boolean_true",
        default=True,
        expected="True",
    ),
    FormatDefaultFixture(
        test_id="boolean_false",
        default=False,
        expected="False",
    ),
]


@pytest.mark.parametrize(
    FormatDefaultFixture._fields,
    FORMAT_DEFAULT_FIXTURES,
    ids=[f.test_id for f in FORMAT_DEFAULT_FIXTURES],
)
def test_format_default(test_id: str, default: t.Any, expected: str | None) -> None:
    """Test default value formatting."""
    assert _format_default(default) == expected


# --- _get_type_name tests ---


def test_get_type_name_int() -> None:
    """Test type name extraction for int."""
    parser = argparse.ArgumentParser()
    action = parser.add_argument("--count", type=int)
    assert _get_type_name(action) == "int"


def test_get_type_name_float() -> None:
    """Test type name extraction for float."""
    parser = argparse.ArgumentParser()
    action = parser.add_argument("--ratio", type=float)
    assert _get_type_name(action) == "float"


def test_get_type_name_str() -> None:
    """Test type name extraction for str."""
    parser = argparse.ArgumentParser()
    action = parser.add_argument("--name", type=str)
    assert _get_type_name(action) == "str"


def test_get_type_name_none() -> None:
    """Test type name extraction when no type specified."""
    parser = argparse.ArgumentParser()
    action = parser.add_argument("--name")
    assert _get_type_name(action) is None


def test_get_type_name_callable() -> None:
    """Test type name extraction for callable types."""
    from pathlib import Path

    parser = argparse.ArgumentParser()
    action = parser.add_argument("--path", type=Path)
    assert _get_type_name(action) == "Path"


# --- _get_action_name tests ---


class ActionNameFixture(t.NamedTuple):
    """Test fixture for _get_action_name function."""

    test_id: str
    action_kwargs: dict[str, t.Any]
    expected: str


ACTION_NAME_FIXTURES: list[ActionNameFixture] = [
    ActionNameFixture(
        test_id="store_default",
        action_kwargs={"dest": "name"},
        expected="store",
    ),
    ActionNameFixture(
        test_id="store_true",
        action_kwargs={"action": "store_true", "dest": "flag"},
        expected="store_true",
    ),
    ActionNameFixture(
        test_id="store_false",
        action_kwargs={"action": "store_false", "dest": "flag"},
        expected="store_false",
    ),
    ActionNameFixture(
        test_id="store_const",
        action_kwargs={"action": "store_const", "const": "value", "dest": "const"},
        expected="store_const",
    ),
    ActionNameFixture(
        test_id="append",
        action_kwargs={"action": "append", "dest": "items"},
        expected="append",
    ),
    ActionNameFixture(
        test_id="count",
        action_kwargs={"action": "count", "dest": "verbose"},
        expected="count",
    ),
]


@pytest.mark.parametrize(
    ActionNameFixture._fields,
    ACTION_NAME_FIXTURES,
    ids=[f.test_id for f in ACTION_NAME_FIXTURES],
)
def test_get_action_name(
    test_id: str, action_kwargs: dict[str, t.Any], expected: str
) -> None:
    """Test action name extraction."""
    parser = argparse.ArgumentParser()
    action = parser.add_argument("--test", **action_kwargs)
    assert _get_action_name(action) == expected


# --- _extract_argument tests ---


def test_extract_argument_positional() -> None:
    """Test extracting a positional argument."""
    parser = argparse.ArgumentParser()
    action = parser.add_argument("filename", help="Input file")
    info = _extract_argument(action)

    assert info.names == ["filename"]
    assert info.help == "Input file"
    assert info.is_positional is True
    assert info.required is True


def test_extract_argument_optional() -> None:
    """Test extracting an optional argument."""
    parser = argparse.ArgumentParser()
    action = parser.add_argument("-v", "--verbose", action="store_true", help="Verbose")
    info = _extract_argument(action)

    assert info.names == ["-v", "--verbose"]
    assert info.action == "store_true"
    assert info.is_positional is False
    assert info.required is False


def test_extract_argument_with_choices() -> None:
    """Test extracting argument with choices."""
    parser = argparse.ArgumentParser()
    action = parser.add_argument("--format", choices=["json", "yaml", "xml"])
    info = _extract_argument(action)

    assert info.choices == ["json", "yaml", "xml"]


def test_extract_argument_with_metavar() -> None:
    """Test extracting argument with metavar."""
    parser = argparse.ArgumentParser()
    action = parser.add_argument("--output", metavar="FILE")
    info = _extract_argument(action)

    assert info.metavar == "FILE"


def test_extract_argument_tuple_metavar() -> None:
    """Test extracting argument with tuple metavar."""
    parser = argparse.ArgumentParser()
    action = parser.add_argument("--range", nargs=2, metavar=("MIN", "MAX"))
    info = _extract_argument(action)

    assert info.metavar == "MIN MAX"


def test_extract_argument_suppressed_help() -> None:
    """Test extracting argument with suppressed help."""
    parser = argparse.ArgumentParser()
    action = parser.add_argument("--secret", help=argparse.SUPPRESS)
    info = _extract_argument(action)

    assert info.help is None


# --- extract_parser integration tests ---


def test_extract_parser_simple(simple_parser: argparse.ArgumentParser) -> None:
    """Test extracting a simple parser."""
    info = extract_parser(simple_parser)

    assert info.prog == "myapp"
    assert info.description == "A simple test application"
    assert len(info.argument_groups) >= 1

    # Find arguments
    all_args = [arg for group in info.argument_groups for arg in group.arguments]
    arg_names = [name for arg in all_args for name in arg.names]

    assert "filename" in arg_names
    assert "--verbose" in arg_names or "-v" in arg_names


def test_extract_parser_with_groups(
    parser_with_groups: argparse.ArgumentParser,
) -> None:
    """Test extracting parser with custom groups."""
    info = extract_parser(parser_with_groups)

    group_titles = [g.title for g in info.argument_groups]
    assert "Input Options" in group_titles
    assert "Output Options" in group_titles


def test_extract_parser_with_subcommands(
    parser_with_subcommands: argparse.ArgumentParser,
) -> None:
    """Test extracting parser with subcommands."""
    info = extract_parser(parser_with_subcommands)

    assert info.subcommands is not None
    assert len(info.subcommands) == 2

    subcmd_names = [s.name for s in info.subcommands]
    assert "sync" in subcmd_names
    assert "add" in subcmd_names

    # Check alias
    add_cmd = next(s for s in info.subcommands if s.name == "add")
    assert "a" in add_cmd.aliases


def test_extract_parser_with_mutex(parser_with_mutex: argparse.ArgumentParser) -> None:
    """Test extracting parser with mutually exclusive group."""
    info = extract_parser(parser_with_mutex)

    # Find the group with mutex
    for group in info.argument_groups:
        if group.mutually_exclusive:
            mutex = group.mutually_exclusive[0]
            assert mutex.required is True
            assert len(mutex.arguments) == 2
            return

    pytest.fail("No mutually exclusive group found")


def test_extract_parser_with_all_actions(
    parser_with_all_actions: argparse.ArgumentParser,
) -> None:
    """Test extracting parser with all action types."""
    info = extract_parser(parser_with_all_actions)

    all_args = [arg for group in info.argument_groups for arg in group.arguments]
    actions = {arg.dest: arg.action for arg in all_args}

    assert actions.get("name") == "store"
    assert actions.get("enable") == "store_const"
    assert actions.get("flag") == "store_true"
    assert actions.get("item") == "append"
    assert actions.get("verbose") == "count"


def test_extract_parser_with_types(
    parser_with_types: argparse.ArgumentParser,
) -> None:
    """Test extracting parser with typed arguments."""
    info = extract_parser(parser_with_types)

    all_args = [arg for group in info.argument_groups for arg in group.arguments]
    types = {arg.dest: arg.type_name for arg in all_args}

    assert types.get("count") == "int"
    assert types.get("ratio") == "float"
    assert types.get("path") == "Path"


def test_extract_parser_with_nargs(
    parser_with_nargs: argparse.ArgumentParser,
) -> None:
    """Test extracting parser with nargs variants."""
    info = extract_parser(parser_with_nargs)

    all_args = [arg for group in info.argument_groups for arg in group.arguments]
    nargs_map = {arg.dest: arg.nargs for arg in all_args}

    assert nargs_map.get("optional") == "?"
    assert nargs_map.get("zero_or_more") == "*"
    assert nargs_map.get("one_or_more") == "+"
    assert nargs_map.get("exactly_two") == 2


def test_extract_parser_with_defaults(
    parser_with_defaults: argparse.ArgumentParser,
) -> None:
    """Test extracting parser with various defaults."""
    info = extract_parser(parser_with_defaults)

    all_args = [arg for group in info.argument_groups for arg in group.arguments]
    defaults = {arg.dest: arg.default_string for arg in all_args}

    assert defaults.get("none_default") == "None"
    assert defaults.get("string_default") == "hello"
    assert defaults.get("int_default") == "42"
    # Suppressed default should have None default_string
    assert "suppress" not in defaults or defaults.get("suppress") is None


def test_extract_parser_nested_subcommands(
    nested_subcommands_parser: argparse.ArgumentParser,
) -> None:
    """Test extracting parser with nested subcommands."""
    info = extract_parser(nested_subcommands_parser)

    assert info.subcommands is not None
    assert len(info.subcommands) == 1

    repo = info.subcommands[0]
    assert repo.name == "repo"
    assert repo.parser.subcommands is not None
    assert len(repo.parser.subcommands) == 2


def test_extract_parser_usage_generation() -> None:
    """Test usage string generation."""
    parser = argparse.ArgumentParser(prog="test")
    parser.add_argument("file")
    parser.add_argument("-v", "--verbose", action="store_true")

    info = extract_parser(parser)

    assert "test" in info.bare_usage
    assert "file" in info.bare_usage


def test_extract_parser_custom_usage() -> None:
    """Test parser with custom usage string."""
    parser = argparse.ArgumentParser(prog="test", usage="test [options] file")

    info = extract_parser(parser)

    assert info.usage == "test [options] file"


def test_extract_parser_with_epilog() -> None:
    """Test parser with epilog."""
    parser = argparse.ArgumentParser(
        prog="test",
        epilog="For more info, see docs.",
    )

    info = extract_parser(parser)

    assert info.epilog == "For more info, see docs."


# --- ArgumentInfo property tests ---


def test_argument_info_is_positional_true() -> None:
    """Test is_positional for positional argument."""
    info = ArgumentInfo(
        names=["filename"],
        help=None,
        default=None,
        default_string=None,
        choices=None,
        required=True,
        metavar=None,
        nargs=None,
        action="store",
        type_name=None,
        const=None,
        dest="filename",
    )
    assert info.is_positional is True


def test_argument_info_is_positional_false() -> None:
    """Test is_positional for optional argument."""
    info = ArgumentInfo(
        names=["-f", "--file"],
        help=None,
        default=None,
        default_string=None,
        choices=None,
        required=False,
        metavar=None,
        nargs=None,
        action="store",
        type_name=None,
        const=None,
        dest="file",
    )
    assert info.is_positional is False


def test_argument_info_empty_names() -> None:
    """Test is_positional with empty names list."""
    info = ArgumentInfo(
        names=[],
        help=None,
        default=None,
        default_string=None,
        choices=None,
        required=False,
        metavar=None,
        nargs=None,
        action="store",
        type_name=None,
        const=None,
        dest="empty",
    )
    assert info.is_positional is False


# --- Dataclass tests ---


def test_parser_info_dataclass() -> None:
    """Test ParserInfo dataclass creation."""
    info = ParserInfo(
        prog="test",
        usage=None,
        bare_usage="test [-h]",
        description="Test description",
        epilog="Test epilog",
        argument_groups=[],
        subcommands=None,
        subcommand_dest=None,
    )

    assert info.prog == "test"
    assert info.description == "Test description"


def test_subcommand_info_recursive() -> None:
    """Test SubcommandInfo with nested parser."""
    nested_info = ParserInfo(
        prog="nested",
        usage=None,
        bare_usage="nested [-h]",
        description=None,
        epilog=None,
        argument_groups=[],
        subcommands=None,
        subcommand_dest=None,
    )

    sub = SubcommandInfo(
        name="sub",
        aliases=[],
        help="Subcommand help",
        parser=nested_info,
    )

    assert sub.parser.prog == "nested"
