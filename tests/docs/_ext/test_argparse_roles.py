"""Tests for argparse_roles docutils extension."""

from __future__ import annotations

import typing as t

import pytest
from argparse_roles import (
    cli_choice_role,
    cli_command_role,
    cli_default_role,
    cli_metavar_role,
    cli_option_role,
    normalize_options,
    register_roles,
)
from docutils import nodes

# --- normalize_options tests ---


def test_normalize_options_none() -> None:
    """Test normalize_options with None input."""
    assert normalize_options(None) == {}


def test_normalize_options_dict() -> None:
    """Test normalize_options with dict input."""
    opts = {"class": "custom"}
    assert normalize_options(opts) == {"class": "custom"}


def test_normalize_options_empty_dict() -> None:
    """Test normalize_options with empty dict input."""
    assert normalize_options({}) == {}


# --- CLI Option Role Tests ---


class OptionRoleFixture(t.NamedTuple):
    """Test fixture for CLI option role."""

    test_id: str
    text: str
    expected_classes: list[str]


OPTION_ROLE_FIXTURES: list[OptionRoleFixture] = [
    OptionRoleFixture(
        test_id="long_option",
        text="--verbose",
        expected_classes=["cli-option", "cli-option-long"],
    ),
    OptionRoleFixture(
        test_id="long_option_with_dash",
        text="--no-color",
        expected_classes=["cli-option", "cli-option-long"],
    ),
    OptionRoleFixture(
        test_id="short_option",
        text="-h",
        expected_classes=["cli-option", "cli-option-short"],
    ),
    OptionRoleFixture(
        test_id="short_option_v",
        text="-v",
        expected_classes=["cli-option", "cli-option-short"],
    ),
    OptionRoleFixture(
        test_id="no_dash_prefix",
        text="option",
        expected_classes=["cli-option"],
    ),
]


@pytest.mark.parametrize(
    list(OptionRoleFixture._fields),
    OPTION_ROLE_FIXTURES,
    ids=[f.test_id for f in OPTION_ROLE_FIXTURES],
)
def test_cli_option_role(
    test_id: str,
    text: str,
    expected_classes: list[str],
) -> None:
    """Test CLI option role generates correct node classes."""
    node_list, messages = cli_option_role(
        "cli-option",
        f":cli-option:`{text}`",
        text,
        1,
        None,
    )

    assert len(node_list) == 1
    assert len(messages) == 0

    node = node_list[0]
    assert isinstance(node, nodes.literal)
    assert node.astext() == text
    assert node["classes"] == expected_classes


def test_cli_option_role_with_options() -> None:
    """Test CLI option role accepts options parameter."""
    node_list, _messages = cli_option_role(
        "cli-option",
        ":cli-option:`--test`",
        "--test",
        1,
        None,
        options={"class": "extra"},
    )

    assert len(node_list) == 1
    # Options are normalized but classes come from role logic
    assert "cli-option" in node_list[0]["classes"]


# --- CLI Metavar Role Tests ---


class MetavarRoleFixture(t.NamedTuple):
    """Test fixture for CLI metavar role."""

    test_id: str
    text: str


METAVAR_ROLE_FIXTURES: list[MetavarRoleFixture] = [
    MetavarRoleFixture(test_id="file", text="FILE"),
    MetavarRoleFixture(test_id="path", text="PATH"),
    MetavarRoleFixture(test_id="directory", text="DIRECTORY"),
    MetavarRoleFixture(test_id="config", text="CONFIG"),
    MetavarRoleFixture(test_id="lowercase", text="value"),
]


@pytest.mark.parametrize(
    list(MetavarRoleFixture._fields),
    METAVAR_ROLE_FIXTURES,
    ids=[f.test_id for f in METAVAR_ROLE_FIXTURES],
)
def test_cli_metavar_role(
    test_id: str,
    text: str,
) -> None:
    """Test CLI metavar role generates correct node."""
    node_list, messages = cli_metavar_role(
        "cli-metavar",
        f":cli-metavar:`{text}`",
        text,
        1,
        None,
    )

    assert len(node_list) == 1
    assert len(messages) == 0

    node = node_list[0]
    assert isinstance(node, nodes.literal)
    assert node.astext() == text
    assert node["classes"] == ["cli-metavar"]


# --- CLI Command Role Tests ---


class CommandRoleFixture(t.NamedTuple):
    """Test fixture for CLI command role."""

    test_id: str
    text: str


COMMAND_ROLE_FIXTURES: list[CommandRoleFixture] = [
    CommandRoleFixture(test_id="sync", text="sync"),
    CommandRoleFixture(test_id="add", text="add"),
    CommandRoleFixture(test_id="vcspull", text="vcspull"),
    CommandRoleFixture(test_id="list", text="list"),
    CommandRoleFixture(test_id="with_dash", text="repo-add"),
]


@pytest.mark.parametrize(
    list(CommandRoleFixture._fields),
    COMMAND_ROLE_FIXTURES,
    ids=[f.test_id for f in COMMAND_ROLE_FIXTURES],
)
def test_cli_command_role(
    test_id: str,
    text: str,
) -> None:
    """Test CLI command role generates correct node."""
    node_list, messages = cli_command_role(
        "cli-command",
        f":cli-command:`{text}`",
        text,
        1,
        None,
    )

    assert len(node_list) == 1
    assert len(messages) == 0

    node = node_list[0]
    assert isinstance(node, nodes.literal)
    assert node.astext() == text
    assert node["classes"] == ["cli-command"]


# --- CLI Default Role Tests ---


class DefaultRoleFixture(t.NamedTuple):
    """Test fixture for CLI default role."""

    test_id: str
    text: str


DEFAULT_ROLE_FIXTURES: list[DefaultRoleFixture] = [
    DefaultRoleFixture(test_id="none", text="None"),
    DefaultRoleFixture(test_id="quoted_auto", text='"auto"'),
    DefaultRoleFixture(test_id="number", text="0"),
    DefaultRoleFixture(test_id="empty_string", text='""'),
    DefaultRoleFixture(test_id="true", text="True"),
    DefaultRoleFixture(test_id="false", text="False"),
]


@pytest.mark.parametrize(
    list(DefaultRoleFixture._fields),
    DEFAULT_ROLE_FIXTURES,
    ids=[f.test_id for f in DEFAULT_ROLE_FIXTURES],
)
def test_cli_default_role(
    test_id: str,
    text: str,
) -> None:
    """Test CLI default role generates correct node."""
    node_list, messages = cli_default_role(
        "cli-default",
        f":cli-default:`{text}`",
        text,
        1,
        None,
    )

    assert len(node_list) == 1
    assert len(messages) == 0

    node = node_list[0]
    assert isinstance(node, nodes.literal)
    assert node.astext() == text
    assert node["classes"] == ["cli-default"]


# --- CLI Choice Role Tests ---


class ChoiceRoleFixture(t.NamedTuple):
    """Test fixture for CLI choice role."""

    test_id: str
    text: str


CHOICE_ROLE_FIXTURES: list[ChoiceRoleFixture] = [
    ChoiceRoleFixture(test_id="json", text="json"),
    ChoiceRoleFixture(test_id="yaml", text="yaml"),
    ChoiceRoleFixture(test_id="table", text="table"),
    ChoiceRoleFixture(test_id="auto", text="auto"),
    ChoiceRoleFixture(test_id="always", text="always"),
    ChoiceRoleFixture(test_id="never", text="never"),
]


@pytest.mark.parametrize(
    list(ChoiceRoleFixture._fields),
    CHOICE_ROLE_FIXTURES,
    ids=[f.test_id for f in CHOICE_ROLE_FIXTURES],
)
def test_cli_choice_role(
    test_id: str,
    text: str,
) -> None:
    """Test CLI choice role generates correct node."""
    node_list, messages = cli_choice_role(
        "cli-choice",
        f":cli-choice:`{text}`",
        text,
        1,
        None,
    )

    assert len(node_list) == 1
    assert len(messages) == 0

    node = node_list[0]
    assert isinstance(node, nodes.literal)
    assert node.astext() == text
    assert node["classes"] == ["cli-choice"]


# --- Register Roles Test ---


def test_register_roles() -> None:
    """Test register_roles doesn't raise errors."""
    # This should not raise any exceptions
    register_roles()


# --- Role Return Type Tests ---


def test_all_roles_return_correct_types() -> None:
    """Test all roles return proper tuple of (nodes, messages)."""
    role_functions = [
        cli_option_role,
        cli_metavar_role,
        cli_command_role,
        cli_default_role,
        cli_choice_role,
    ]

    for role_func in role_functions:
        result = role_func("test", ":test:`value`", "value", 1, None)

        assert isinstance(result, tuple), f"{role_func.__name__} should return tuple"
        assert len(result) == 2, f"{role_func.__name__} should return 2-tuple"

        node_list, messages = result
        assert isinstance(node_list, list), (
            f"{role_func.__name__} first element should be list"
        )
        assert isinstance(messages, list), (
            f"{role_func.__name__} second element should be list"
        )
        assert len(node_list) == 1, f"{role_func.__name__} should return one node"
        assert len(messages) == 0, (
            f"{role_func.__name__} should return no error messages"
        )


# --- Node Structure Tests ---


def test_cli_option_node_structure() -> None:
    """Test CLI option node has expected structure."""
    node_list, _ = cli_option_role(
        "cli-option",
        ":cli-option:`--test`",
        "--test",
        1,
        None,
    )

    node = node_list[0]

    # Check node type
    assert isinstance(node, nodes.literal)

    # Check rawsource is preserved
    assert node.rawsource == ":cli-option:`--test`"

    # Check text content
    assert len(node.children) == 1
    assert isinstance(node.children[0], nodes.Text)
    assert str(node.children[0]) == "--test"


def test_roles_with_none_content_parameter() -> None:
    """Test roles handle None content parameter correctly."""
    node_list, messages = cli_option_role(
        "cli-option",
        ":cli-option:`--test`",
        "--test",
        1,
        None,
        options=None,
        content=None,
    )

    assert len(node_list) == 1
    assert len(messages) == 0


def test_roles_with_empty_content_parameter() -> None:
    """Test roles handle empty content parameter correctly."""
    node_list, messages = cli_option_role(
        "cli-option",
        ":cli-option:`--test`",
        "--test",
        1,
        None,
        options={},
        content=[],
    )

    assert len(node_list) == 1
    assert len(messages) == 0


# --- Edge Case Tests ---


def test_cli_option_role_empty_text() -> None:
    """Test CLI option role with empty text."""
    node_list, _messages = cli_option_role(
        "cli-option",
        ":cli-option:``",
        "",
        1,
        None,
    )

    assert len(node_list) == 1
    assert node_list[0].astext() == ""
    # No dash prefix, so only base class
    assert node_list[0]["classes"] == ["cli-option"]


def test_cli_option_role_special_characters() -> None:
    """Test CLI option role with special characters in text."""
    node_list, _messages = cli_option_role(
        "cli-option",
        ":cli-option:`--foo-bar_baz`",
        "--foo-bar_baz",
        1,
        None,
    )

    assert len(node_list) == 1
    assert node_list[0].astext() == "--foo-bar_baz"
    assert "cli-option-long" in node_list[0]["classes"]
