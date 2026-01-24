"""Tests for cli_usage_lexer Pygments extension."""

from __future__ import annotations

import typing as t

import pytest
from cli_usage_lexer import (
    CLIUsageLexer,
    tokenize_usage,
)

# --- Helper to extract token type names ---


def get_tokens(text: str) -> list[tuple[str, str]]:
    """Get tokens as (type_name, value) tuples."""
    lexer = CLIUsageLexer()
    return [
        (str(tok_type), tok_value) for tok_type, tok_value in lexer.get_tokens(text)
    ]


# --- Token type fixtures ---


class TokenTypeFixture(t.NamedTuple):
    """Test fixture for verifying specific token types."""

    test_id: str
    input_text: str
    expected_token_type: str
    expected_value: str


TOKEN_TYPE_FIXTURES: list[TokenTypeFixture] = [
    TokenTypeFixture(
        test_id="usage_heading",
        input_text="usage:",
        expected_token_type="Token.Generic.Heading",
        expected_value="usage:",
    ),
    TokenTypeFixture(
        test_id="short_option",
        input_text="-h",
        expected_token_type="Token.Name.Attribute",
        expected_value="-h",
    ),
    TokenTypeFixture(
        test_id="long_option",
        input_text="--verbose",
        expected_token_type="Token.Name.Tag",
        expected_value="--verbose",
    ),
    TokenTypeFixture(
        test_id="long_option_with_dashes",
        input_text="--no-color",
        expected_token_type="Token.Name.Tag",
        expected_value="--no-color",
    ),
    TokenTypeFixture(
        test_id="uppercase_metavar",
        input_text="COMMAND",
        expected_token_type="Token.Name.Constant",
        expected_value="COMMAND",
    ),
    TokenTypeFixture(
        test_id="uppercase_metavar_with_underscore",
        input_text="FILE_PATH",
        expected_token_type="Token.Name.Constant",
        expected_value="FILE_PATH",
    ),
    TokenTypeFixture(
        test_id="positional_arg",
        input_text="repo-name",
        expected_token_type="Token.Name.Label",
        expected_value="repo-name",
    ),
    TokenTypeFixture(
        test_id="command_name",
        input_text="vcspull",
        expected_token_type="Token.Name.Label",
        expected_value="vcspull",
    ),
    TokenTypeFixture(
        test_id="open_bracket",
        input_text="[",
        expected_token_type="Token.Punctuation",
        expected_value="[",
    ),
    TokenTypeFixture(
        test_id="close_bracket",
        input_text="]",
        expected_token_type="Token.Punctuation",
        expected_value="]",
    ),
    TokenTypeFixture(
        test_id="pipe_operator",
        input_text="|",
        expected_token_type="Token.Operator",
        expected_value="|",
    ),
]


@pytest.mark.parametrize(
    TokenTypeFixture._fields,
    TOKEN_TYPE_FIXTURES,
    ids=[f.test_id for f in TOKEN_TYPE_FIXTURES],
)
def test_token_type(
    test_id: str,
    input_text: str,
    expected_token_type: str,
    expected_value: str,
) -> None:
    """Test individual token type detection."""
    tokens = get_tokens(input_text)
    # Find the expected token (skip whitespace)
    non_ws_tokens = [(t, v) for t, v in tokens if "Whitespace" not in t and v.strip()]
    assert len(non_ws_tokens) >= 1, f"No non-whitespace tokens found for '{input_text}'"
    token_type, token_value = non_ws_tokens[0]
    assert token_type == expected_token_type, (
        f"Expected {expected_token_type}, got {token_type}"
    )
    assert token_value == expected_value


# --- Short option with value fixtures ---


class ShortOptionValueFixture(t.NamedTuple):
    """Test fixture for short options with values."""

    test_id: str
    input_text: str
    option: str
    value: str


SHORT_OPTION_VALUE_FIXTURES: list[ShortOptionValueFixture] = [
    ShortOptionValueFixture(
        test_id="lowercase_value",
        input_text="-c config-path",
        option="-c",
        value="config-path",
    ),
    ShortOptionValueFixture(
        test_id="uppercase_value",
        input_text="-d DIRECTORY",
        option="-d",
        value="DIRECTORY",
    ),
    ShortOptionValueFixture(
        test_id="simple_value",
        input_text="-r name",
        option="-r",
        value="name",
    ),
]


@pytest.mark.parametrize(
    ShortOptionValueFixture._fields,
    SHORT_OPTION_VALUE_FIXTURES,
    ids=[f.test_id for f in SHORT_OPTION_VALUE_FIXTURES],
)
def test_short_option_with_value(
    test_id: str,
    input_text: str,
    option: str,
    value: str,
) -> None:
    """Test short option followed by value tokenization."""
    tokens = get_tokens(input_text)
    non_ws_tokens = [(t, v) for t, v in tokens if "Whitespace" not in t]

    assert len(non_ws_tokens) >= 2
    assert non_ws_tokens[0] == ("Token.Name.Attribute", option)
    # Value could be Name.Variable or Name.Constant depending on case
    assert non_ws_tokens[1][1] == value


# --- Long option with value fixtures ---


class LongOptionValueFixture(t.NamedTuple):
    """Test fixture for long options with = values."""

    test_id: str
    input_text: str
    option: str
    value: str


LONG_OPTION_VALUE_FIXTURES: list[LongOptionValueFixture] = [
    LongOptionValueFixture(
        test_id="uppercase_value",
        input_text="--config=FILE",
        option="--config",
        value="FILE",
    ),
    LongOptionValueFixture(
        test_id="lowercase_value",
        input_text="--output=path",
        option="--output",
        value="path",
    ),
]


@pytest.mark.parametrize(
    LongOptionValueFixture._fields,
    LONG_OPTION_VALUE_FIXTURES,
    ids=[f.test_id for f in LONG_OPTION_VALUE_FIXTURES],
)
def test_long_option_with_value(
    test_id: str,
    input_text: str,
    option: str,
    value: str,
) -> None:
    """Test long option with = value tokenization."""
    tokens = get_tokens(input_text)
    non_ws_tokens = [(t, v) for t, v in tokens if "Whitespace" not in t]

    assert len(non_ws_tokens) >= 3
    assert non_ws_tokens[0] == ("Token.Name.Tag", option)
    assert non_ws_tokens[1] == ("Token.Operator", "=")
    assert non_ws_tokens[2][1] == value


# --- Full usage string fixtures ---


class UsageStringFixture(t.NamedTuple):
    """Test fixture for full usage string tokenization."""

    test_id: str
    input_text: str
    expected_contains: list[tuple[str, str]]


USAGE_STRING_FIXTURES: list[UsageStringFixture] = [
    UsageStringFixture(
        test_id="simple_usage",
        input_text="usage: cmd [-h]",
        expected_contains=[
            ("Token.Generic.Heading", "usage:"),
            ("Token.Name.Label", "cmd"),
            ("Token.Punctuation", "["),
            ("Token.Name.Attribute", "-h"),
            ("Token.Punctuation", "]"),
        ],
    ),
    UsageStringFixture(
        test_id="mutually_exclusive",
        input_text="[--json | --ndjson | --table]",
        expected_contains=[
            ("Token.Name.Tag", "--json"),
            ("Token.Operator", "|"),
            ("Token.Name.Tag", "--ndjson"),
            ("Token.Operator", "|"),
            ("Token.Name.Tag", "--table"),
        ],
    ),
    UsageStringFixture(
        test_id="subcommand",
        input_text="usage: vcspull sync",
        expected_contains=[
            ("Token.Generic.Heading", "usage:"),
            ("Token.Name.Label", "vcspull"),
            ("Token.Name.Label", "sync"),
        ],
    ),
    UsageStringFixture(
        test_id="positional_args",
        input_text="[repo-name] [path]",
        expected_contains=[
            ("Token.Punctuation", "["),
            ("Token.Name.Label", "repo-name"),
            ("Token.Punctuation", "]"),
            ("Token.Punctuation", "["),
            ("Token.Name.Label", "path"),
            ("Token.Punctuation", "]"),
        ],
    ),
]


@pytest.mark.parametrize(
    UsageStringFixture._fields,
    USAGE_STRING_FIXTURES,
    ids=[f.test_id for f in USAGE_STRING_FIXTURES],
)
def test_usage_string(
    test_id: str,
    input_text: str,
    expected_contains: list[tuple[str, str]],
) -> None:
    """Test full usage string tokenization contains expected tokens."""
    tokens = get_tokens(input_text)
    for expected_type, expected_value in expected_contains:
        assert (expected_type, expected_value) in tokens, (
            f"Expected ({expected_type}, {expected_value!r}) not found in tokens"
        )


# --- Real vcspull usage output test ---


def test_vcspull_sync_usage() -> None:
    """Test real vcspull sync usage output tokenization."""
    usage_text = """\
usage: vcspull sync [-h] [-c CONFIG] [-d DIRECTORY]
                    [--json | --ndjson | --table] [--color {auto,always,never}]
                    [--no-progress] [--verbose]
                    [repo-name] [path]"""

    tokens = get_tokens(usage_text)

    # Check key elements are present
    # Note: DIRECTORY after -d is Name.Variable (option value), not Name.Constant
    expected = [
        ("Token.Generic.Heading", "usage:"),
        ("Token.Name.Label", "vcspull"),
        ("Token.Name.Label", "sync"),
        ("Token.Name.Attribute", "-h"),
        ("Token.Name.Attribute", "-c"),
        ("Token.Name.Variable", "CONFIG"),  # Option value, not standalone metavar
        ("Token.Name.Attribute", "-d"),
        ("Token.Name.Variable", "DIRECTORY"),  # Option value, not standalone metavar
        ("Token.Name.Tag", "--json"),
        ("Token.Name.Tag", "--ndjson"),
        ("Token.Name.Tag", "--table"),
        ("Token.Name.Tag", "--color"),
        ("Token.Name.Tag", "--no-progress"),
        ("Token.Name.Tag", "--verbose"),
        ("Token.Name.Label", "repo-name"),
        ("Token.Name.Label", "path"),
    ]

    for expected_type, expected_value in expected:
        assert (expected_type, expected_value) in tokens, (
            f"Expected ({expected_type}, {expected_value!r}) not in tokens"
        )


# --- tokenize_usage helper function test ---


def test_tokenize_usage_helper() -> None:
    """Test the tokenize_usage helper function."""
    result = tokenize_usage("usage: cmd [-h]")

    assert result[0] == ("Token.Generic.Heading", "usage:")
    assert ("Token.Name.Label", "cmd") in result
    assert ("Token.Name.Attribute", "-h") in result
