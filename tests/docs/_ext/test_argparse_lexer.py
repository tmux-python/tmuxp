"""Tests for argparse_lexer Pygments extension."""

from __future__ import annotations

import typing as t

import pytest
from argparse_lexer import (
    ArgparseHelpLexer,
    ArgparseLexer,
    ArgparseUsageLexer,
    tokenize_argparse,
    tokenize_usage,
)

# --- Helper to extract token type names ---


def get_tokens(text: str, lexer_class: type = ArgparseLexer) -> list[tuple[str, str]]:
    """Get tokens as (type_name, value) tuples.

    Examples
    --------
    >>> tokens = get_tokens("usage: cmd [-h]")
    >>> any(t[0] == "Token.Name.Attribute" for t in tokens)
    True
    """
    lexer = lexer_class()
    return [
        (str(tok_type), tok_value) for tok_type, tok_value in lexer.get_tokens(text)
    ]


def get_usage_tokens(text: str) -> list[tuple[str, str]]:
    """Get tokens using ArgparseUsageLexer.

    Examples
    --------
    >>> tokens = get_usage_tokens("usage: cmd")
    >>> tokens[0]
    ('Token.Generic.Heading', 'usage:')
    """
    return get_tokens(text, ArgparseUsageLexer)


def get_help_tokens(text: str) -> list[tuple[str, str]]:
    """Get tokens using ArgparseHelpLexer.

    Examples
    --------
    >>> tokens = get_help_tokens("positional arguments:")
    >>> any("Subheading" in t[0] for t in tokens)
    True
    """
    return get_tokens(text, ArgparseHelpLexer)


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
        test_id="short_option_v",
        input_text="-v",
        expected_token_type="Token.Name.Attribute",
        expected_value="-v",
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
        input_text="FILE",
        expected_token_type="Token.Name.Variable",
        expected_value="FILE",
    ),
    TokenTypeFixture(
        test_id="uppercase_metavar_path",
        input_text="PATH",
        expected_token_type="Token.Name.Variable",
        expected_value="PATH",
    ),
    TokenTypeFixture(
        test_id="uppercase_metavar_with_underscore",
        input_text="FILE_PATH",
        expected_token_type="Token.Name.Variable",
        expected_value="FILE_PATH",
    ),
    TokenTypeFixture(
        test_id="command_name",
        input_text="sync",
        expected_token_type="Token.Name.Label",
        expected_value="sync",
    ),
    TokenTypeFixture(
        test_id="command_with_dash",
        input_text="repo-name",
        expected_token_type="Token.Name.Label",
        expected_value="repo-name",
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
        test_id="open_paren",
        input_text="(",
        expected_token_type="Token.Punctuation",
        expected_value="(",
    ),
    TokenTypeFixture(
        test_id="close_paren",
        input_text=")",
        expected_token_type="Token.Punctuation",
        expected_value=")",
    ),
    TokenTypeFixture(
        test_id="open_brace",
        input_text="{",
        expected_token_type="Token.Punctuation",
        expected_value="{",
    ),
    TokenTypeFixture(
        test_id="pipe_operator",
        input_text="|",
        expected_token_type="Token.Operator",
        expected_value="|",
    ),
    TokenTypeFixture(
        test_id="ellipsis",
        input_text="...",
        expected_token_type="Token.Punctuation",
        expected_value="...",
    ),
]


@pytest.mark.parametrize(
    list(TokenTypeFixture._fields),
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
    tokens = get_usage_tokens(input_text)
    # Find the expected token (skip whitespace)
    non_ws_tokens = [(t, v) for t, v in tokens if "Whitespace" not in t and v.strip()]
    assert len(non_ws_tokens) >= 1, f"No non-whitespace tokens found for '{input_text}'"
    token_type, token_value = non_ws_tokens[0]
    assert token_type == expected_token_type, (
        f"Expected {expected_token_type}, got {token_type}"
    )
    assert token_value == expected_value


# --- Choice fixtures ---


class ChoiceFixture(t.NamedTuple):
    """Test fixture for choice enumeration patterns."""

    test_id: str
    input_text: str
    expected_choices: list[str]


CHOICE_FIXTURES: list[ChoiceFixture] = [
    ChoiceFixture(
        test_id="simple_choices",
        input_text="{json,yaml,table}",
        expected_choices=["json", "yaml", "table"],
    ),
    ChoiceFixture(
        test_id="numeric_choices",
        input_text="{1,2,3}",
        expected_choices=["1", "2", "3"],
    ),
    ChoiceFixture(
        test_id="auto_always_never",
        input_text="{auto,always,never}",
        expected_choices=["auto", "always", "never"],
    ),
    ChoiceFixture(
        test_id="two_choices",
        input_text="{a,b}",
        expected_choices=["a", "b"],
    ),
]


@pytest.mark.parametrize(
    list(ChoiceFixture._fields),
    CHOICE_FIXTURES,
    ids=[f.test_id for f in CHOICE_FIXTURES],
)
def test_choices(
    test_id: str,
    input_text: str,
    expected_choices: list[str],
) -> None:
    """Test choice enumeration tokenization."""
    tokens = get_usage_tokens(input_text)
    # Extract choice values (Name.Constant tokens)
    choice_tokens = [v for t, v in tokens if t == "Token.Name.Constant"]
    assert choice_tokens == expected_choices


# --- Mutex group fixtures ---


class MutexGroupFixture(t.NamedTuple):
    """Test fixture for mutually exclusive group patterns."""

    test_id: str
    input_text: str
    expected_options: list[str]
    is_required: bool


MUTEX_GROUP_FIXTURES: list[MutexGroupFixture] = [
    MutexGroupFixture(
        test_id="optional_short",
        input_text="[-a | -b | -c]",
        expected_options=["-a", "-b", "-c"],
        is_required=False,
    ),
    MutexGroupFixture(
        test_id="optional_long",
        input_text="[--foo FOO | --bar BAR]",
        expected_options=["--foo", "--bar"],
        is_required=False,
    ),
    MutexGroupFixture(
        test_id="required_long",
        input_text="(--foo | --bar)",
        expected_options=["--foo", "--bar"],
        is_required=True,
    ),
    MutexGroupFixture(
        test_id="required_with_metavar",
        input_text="(--input FILE | --stdin)",
        expected_options=["--input", "--stdin"],
        is_required=True,
    ),
    MutexGroupFixture(
        test_id="optional_output_formats",
        input_text="[--json | --ndjson | --table]",
        expected_options=["--json", "--ndjson", "--table"],
        is_required=False,
    ),
]


@pytest.mark.parametrize(
    list(MutexGroupFixture._fields),
    MUTEX_GROUP_FIXTURES,
    ids=[f.test_id for f in MUTEX_GROUP_FIXTURES],
)
def test_mutex_groups(
    test_id: str,
    input_text: str,
    expected_options: list[str],
    is_required: bool,
) -> None:
    """Test mutually exclusive group tokenization."""
    tokens = get_usage_tokens(input_text)

    # Check for proper brackets (required uses parens, optional uses brackets)
    if is_required:
        assert ("Token.Punctuation", "(") in tokens
        assert ("Token.Punctuation", ")") in tokens
    else:
        assert ("Token.Punctuation", "[") in tokens
        assert ("Token.Punctuation", "]") in tokens

    # Check pipe operators present
    pipe_count = sum(1 for t, v in tokens if t == "Token.Operator" and v == "|")
    assert pipe_count == len(expected_options) - 1

    # Check options are present
    for opt in expected_options:
        if opt.startswith("--"):
            assert ("Token.Name.Tag", opt) in tokens
        else:
            assert ("Token.Name.Attribute", opt) in tokens


# --- Nargs pattern fixtures ---


class NargsFixture(t.NamedTuple):
    """Test fixture for nargs/variadic patterns."""

    test_id: str
    input_text: str
    has_ellipsis: bool
    has_metavar: str | None


NARGS_FIXTURES: list[NargsFixture] = [
    NargsFixture(
        test_id="nargs_plus",
        input_text="FILE ...",
        has_ellipsis=True,
        has_metavar="FILE",
    ),
    NargsFixture(
        test_id="nargs_star",
        input_text="[FILE ...]",
        has_ellipsis=True,
        has_metavar="FILE",
    ),
    NargsFixture(
        test_id="nargs_question",
        input_text="[--foo [FOO]]",
        has_ellipsis=False,
        has_metavar="FOO",
    ),
    NargsFixture(
        test_id="nargs_plus_with_option",
        input_text="[--bar X [X ...]]",
        has_ellipsis=True,
        has_metavar="X",
    ),
]


@pytest.mark.parametrize(
    list(NargsFixture._fields),
    NARGS_FIXTURES,
    ids=[f.test_id for f in NARGS_FIXTURES],
)
def test_nargs_patterns(
    test_id: str,
    input_text: str,
    has_ellipsis: bool,
    has_metavar: str | None,
) -> None:
    """Test nargs/variadic pattern tokenization."""
    tokens = get_usage_tokens(input_text)

    # Check ellipsis
    ellipsis_present = ("Token.Punctuation", "...") in tokens
    assert ellipsis_present == has_ellipsis

    # Check metavar
    if has_metavar:
        assert ("Token.Name.Variable", has_metavar) in tokens


# --- Long option with value fixtures ---


class LongOptionValueFixture(t.NamedTuple):
    """Test fixture for long options with = values."""

    test_id: str
    input_text: str
    option: str
    value: str


LONG_OPTION_VALUE_FIXTURES: list[LongOptionValueFixture] = [
    LongOptionValueFixture(
        test_id="config_file",
        input_text="--config=FILE",
        option="--config",
        value="FILE",
    ),
    LongOptionValueFixture(
        test_id="log_level",
        input_text="--log-level=DEBUG",
        option="--log-level",
        value="DEBUG",
    ),
    LongOptionValueFixture(
        test_id="lowercase_value",
        input_text="--output=path",
        option="--output",
        value="path",
    ),
]


@pytest.mark.parametrize(
    list(LongOptionValueFixture._fields),
    LONG_OPTION_VALUE_FIXTURES,
    ids=[f.test_id for f in LONG_OPTION_VALUE_FIXTURES],
)
def test_long_option_with_equals_value(
    test_id: str,
    input_text: str,
    option: str,
    value: str,
) -> None:
    """Test long option with = value tokenization."""
    tokens = get_usage_tokens(input_text)
    non_ws_tokens = [(t, v) for t, v in tokens if "Whitespace" not in t]

    assert len(non_ws_tokens) >= 3
    assert non_ws_tokens[0] == ("Token.Name.Tag", option)
    assert non_ws_tokens[1] == ("Token.Operator", "=")
    assert non_ws_tokens[2][1] == value


# --- Short option with value fixtures ---


class ShortOptionValueFixture(t.NamedTuple):
    """Test fixture for short options with space-separated values."""

    test_id: str
    input_text: str
    option: str
    value: str


SHORT_OPTION_VALUE_FIXTURES: list[ShortOptionValueFixture] = [
    ShortOptionValueFixture(
        test_id="config_path",
        input_text="-c config-path",
        option="-c",
        value="config-path",
    ),
    ShortOptionValueFixture(
        test_id="directory",
        input_text="-d DIRECTORY",
        option="-d",
        value="DIRECTORY",
    ),
    ShortOptionValueFixture(
        test_id="simple_name",
        input_text="-r name",
        option="-r",
        value="name",
    ),
    ShortOptionValueFixture(
        test_id="underscore_metavar",
        input_text="-L socket_name",
        option="-L",
        value="socket_name",
    ),
    ShortOptionValueFixture(
        test_id="multiple_underscores",
        input_text="-f tmux_config_file",
        option="-f",
        value="tmux_config_file",
    ),
]


@pytest.mark.parametrize(
    list(ShortOptionValueFixture._fields),
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
    tokens = get_usage_tokens(input_text)
    non_ws_tokens = [(t, v) for t, v in tokens if "Whitespace" not in t]

    assert len(non_ws_tokens) >= 2
    assert non_ws_tokens[0] == ("Token.Name.Attribute", option)
    assert non_ws_tokens[1][1] == value


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
            # Subcommands now use Name.Function per 30ea233
            ("Token.Name.Function", "sync"),
        ],
    ),
    UsageStringFixture(
        test_id="with_choices",
        input_text="usage: cmd {a,b,c}",
        expected_contains=[
            ("Token.Generic.Heading", "usage:"),
            ("Token.Name.Constant", "a"),
            ("Token.Name.Constant", "b"),
            ("Token.Name.Constant", "c"),
        ],
    ),
    UsageStringFixture(
        test_id="complex_usage",
        input_text="usage: prog [-h] [--verbose] FILE ...",
        expected_contains=[
            ("Token.Generic.Heading", "usage:"),
            ("Token.Name.Label", "prog"),
            ("Token.Name.Attribute", "-h"),
            ("Token.Name.Tag", "--verbose"),
            ("Token.Name.Variable", "FILE"),
            ("Token.Punctuation", "..."),
        ],
    ),
]


@pytest.mark.parametrize(
    list(UsageStringFixture._fields),
    USAGE_STRING_FIXTURES,
    ids=[f.test_id for f in USAGE_STRING_FIXTURES],
)
def test_usage_string(
    test_id: str,
    input_text: str,
    expected_contains: list[tuple[str, str]],
) -> None:
    """Test full usage string tokenization contains expected tokens."""
    tokens = get_usage_tokens(input_text)
    for expected_type, expected_value in expected_contains:
        assert (expected_type, expected_value) in tokens, (
            f"Expected ({expected_type}, {expected_value!r}) not found in tokens"
        )


# --- Section header fixtures ---


class SectionHeaderFixture(t.NamedTuple):
    """Test fixture for section header recognition."""

    test_id: str
    input_text: str
    expected_header: str


SECTION_HEADER_FIXTURES: list[SectionHeaderFixture] = [
    SectionHeaderFixture(
        test_id="positional_arguments",
        input_text="positional arguments:",
        expected_header="positional arguments:",
    ),
    SectionHeaderFixture(
        test_id="options",
        input_text="options:",
        expected_header="options:",
    ),
    SectionHeaderFixture(
        test_id="optional_arguments",
        input_text="optional arguments:",
        expected_header="optional arguments:",
    ),
    SectionHeaderFixture(
        test_id="custom_section",
        input_text="advanced options:",
        expected_header="advanced options:",
    ),
]


@pytest.mark.parametrize(
    list(SectionHeaderFixture._fields),
    SECTION_HEADER_FIXTURES,
    ids=[f.test_id for f in SECTION_HEADER_FIXTURES],
)
def test_section_headers(
    test_id: str,
    input_text: str,
    expected_header: str,
) -> None:
    """Test section header tokenization."""
    tokens = get_help_tokens(input_text)
    # Section headers should be Generic.Subheading
    # Strip newlines from token values (lexer may include trailing \n)
    subheading_tokens = [
        v.strip() for t, v in tokens if t == "Token.Generic.Subheading"
    ]
    assert expected_header in subheading_tokens


# --- Full help output test ---


def test_full_help_output() -> None:
    """Test full argparse -h output tokenization."""
    help_text = """\
usage: vcspull sync [-h] [-c CONFIG] [-d DIRECTORY]
                    [--json | --ndjson | --table]
                    [repo-name] [path]

positional arguments:
  repo-name             repository name filter
  path                  path filter

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        config file path
  --json                output as JSON
"""
    tokens = get_help_tokens(help_text)

    # Check usage heading
    assert ("Token.Generic.Heading", "usage:") in tokens

    # Check section headers
    subheadings = [v for t, v in tokens if t == "Token.Generic.Subheading"]
    assert "positional arguments:" in subheadings
    assert "options:" in subheadings

    # Check options are recognized
    assert ("Token.Name.Attribute", "-h") in tokens
    assert ("Token.Name.Tag", "--help") in tokens
    assert ("Token.Name.Tag", "--config") in tokens
    assert ("Token.Name.Tag", "--json") in tokens

    # Check command/positional names
    assert ("Token.Name.Label", "vcspull") in tokens
    # Subcommands now use Name.Function per 30ea233
    assert ("Token.Name.Function", "sync") in tokens


# --- Real vcspull usage output test ---


def test_vcspull_sync_usage() -> None:
    """Test real vcspull sync usage output tokenization."""
    usage_text = """\
usage: vcspull sync [-h] [-c CONFIG] [-d DIRECTORY]
                    [--json | --ndjson | --table] [--color {auto,always,never}]
                    [--no-progress] [--verbose]
                    [repo-name] [path]"""

    tokens = get_usage_tokens(usage_text)

    expected = [
        ("Token.Generic.Heading", "usage:"),
        ("Token.Name.Label", "vcspull"),
        # Subcommands now use Name.Function per 30ea233
        ("Token.Name.Function", "sync"),
        ("Token.Name.Attribute", "-h"),
        ("Token.Name.Attribute", "-c"),
        ("Token.Name.Variable", "CONFIG"),
        ("Token.Name.Attribute", "-d"),
        ("Token.Name.Variable", "DIRECTORY"),
        ("Token.Name.Tag", "--json"),
        ("Token.Name.Tag", "--ndjson"),
        ("Token.Name.Tag", "--table"),
        ("Token.Name.Tag", "--color"),
        ("Token.Name.Tag", "--no-progress"),
        ("Token.Name.Tag", "--verbose"),
        # Optional positional args in brackets also use Name.Function per 30ea233
        ("Token.Name.Function", "repo-name"),
        ("Token.Name.Function", "path"),
    ]

    for expected_type, expected_value in expected:
        assert (expected_type, expected_value) in tokens, (
            f"Expected ({expected_type}, {expected_value!r}) not in tokens"
        )

    # Check choices are properly tokenized
    assert ("Token.Name.Constant", "auto") in tokens
    assert ("Token.Name.Constant", "always") in tokens
    assert ("Token.Name.Constant", "never") in tokens


# --- tokenize_argparse helper function test ---


def test_tokenize_argparse_helper() -> None:
    """Test the tokenize_argparse helper function."""
    result = tokenize_argparse("usage: cmd [-h]")

    assert result[0] == ("Token.Generic.Heading", "usage:")
    assert ("Token.Name.Label", "cmd") in result
    assert ("Token.Name.Attribute", "-h") in result


def test_tokenize_usage_helper() -> None:
    """Test the tokenize_usage helper function."""
    result = tokenize_usage("usage: cmd [-h]")

    assert result[0] == ("Token.Generic.Heading", "usage:")
    assert ("Token.Name.Label", "cmd") in result
    assert ("Token.Name.Attribute", "-h") in result


# --- Lexer class selection tests ---


def test_argparse_lexer_usage_detection() -> None:
    """Test ArgparseLexer handles usage lines correctly."""
    lexer = ArgparseLexer()
    tokens = list(lexer.get_tokens("usage: cmd [-h]"))
    token_types = [str(t) for t, v in tokens]
    assert "Token.Generic.Heading" in token_types


def test_argparse_lexer_section_detection() -> None:
    """Test ArgparseLexer handles section headers correctly."""
    lexer = ArgparseLexer()
    tokens = list(lexer.get_tokens("positional arguments:"))
    token_types = [str(t) for t, v in tokens]
    assert "Token.Generic.Subheading" in token_types


def test_argparse_usage_lexer_standalone() -> None:
    """Test ArgparseUsageLexer works standalone."""
    lexer = ArgparseUsageLexer()
    tokens = list(lexer.get_tokens("usage: cmd [-h] --foo FILE"))
    token_types = [str(t) for t, v in tokens]

    assert "Token.Generic.Heading" in token_types
    assert "Token.Name.Label" in token_types  # cmd
    assert "Token.Name.Attribute" in token_types  # -h
    assert "Token.Name.Tag" in token_types  # --foo


def test_argparse_help_lexer_multiline() -> None:
    """Test ArgparseHelpLexer handles multiline help."""
    lexer = ArgparseHelpLexer()
    help_text = """usage: cmd

options:
  -h  help
"""
    tokens = list(lexer.get_tokens(help_text))
    token_values = [v for t, v in tokens]

    assert "usage:" in token_values
    assert "options:" in token_values or any(
        "options:" in v for v in token_values if isinstance(v, str)
    )


def test_lowercase_metavar_with_underscores() -> None:
    """Test lowercase metavars with underscores are fully captured.

    Regression test: previously `socket_name` was tokenized as `socket` + `_name`.
    Example from tmuxp load usage.
    """
    usage = "usage: prog [-L socket_name] [-S socket_path] [-f config_file]"
    tokens = get_usage_tokens(usage)

    # All underscore metavars should be fully captured
    assert ("Token.Name.Variable", "socket_name") in tokens
    assert ("Token.Name.Variable", "socket_path") in tokens
    assert ("Token.Name.Variable", "config_file") in tokens
