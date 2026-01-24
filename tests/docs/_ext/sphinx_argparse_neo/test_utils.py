"""Tests for sphinx_argparse_neo text processing utilities."""

from __future__ import annotations

import typing as t

import pytest
from sphinx_argparse_neo.utils import escape_rst_emphasis, strip_ansi

# --- strip_ansi tests ---


class StripAnsiFixture(t.NamedTuple):
    """Test fixture for strip_ansi function."""

    test_id: str
    input_text: str
    expected: str


STRIP_ANSI_FIXTURES: list[StripAnsiFixture] = [
    StripAnsiFixture(
        test_id="plain_text",
        input_text="hello",
        expected="hello",
    ),
    StripAnsiFixture(
        test_id="green_color",
        input_text="\033[32mgreen\033[0m",
        expected="green",
    ),
    StripAnsiFixture(
        test_id="bold_blue",
        input_text="\033[1;34mbold\033[0m",
        expected="bold",
    ),
    StripAnsiFixture(
        test_id="multiple_codes",
        input_text="\033[1m\033[32mtest\033[0m",
        expected="test",
    ),
    StripAnsiFixture(
        test_id="empty_string",
        input_text="",
        expected="",
    ),
    StripAnsiFixture(
        test_id="mixed_content",
        input_text="pre\033[31mred\033[0mpost",
        expected="preredpost",
    ),
    StripAnsiFixture(
        test_id="reset_only",
        input_text="\033[0m",
        expected="",
    ),
    StripAnsiFixture(
        test_id="sgr_params",
        input_text="\033[38;5;196mred256\033[0m",
        expected="red256",
    ),
]


@pytest.mark.parametrize(
    StripAnsiFixture._fields,
    STRIP_ANSI_FIXTURES,
    ids=[f.test_id for f in STRIP_ANSI_FIXTURES],
)
def test_strip_ansi(test_id: str, input_text: str, expected: str) -> None:
    """Test ANSI escape code stripping."""
    assert strip_ansi(input_text) == expected


# --- escape_rst_emphasis tests ---


class EscapeRstEmphasisFixture(t.NamedTuple):
    """Test fixture for escape_rst_emphasis function."""

    test_id: str
    input_text: str
    expected: str


ESCAPE_RST_EMPHASIS_FIXTURES: list[EscapeRstEmphasisFixture] = [
    EscapeRstEmphasisFixture(
        test_id="glob_pattern_quoted",
        input_text='tmuxp load "my-*"',
        expected='tmuxp load "my-\\*"',
    ),
    EscapeRstEmphasisFixture(
        test_id="glob_pattern_django",
        input_text="django-*",
        expected="django-\\*",
    ),
    EscapeRstEmphasisFixture(
        test_id="glob_pattern_flask",
        input_text="flask-*",
        expected="flask-\\*",
    ),
    EscapeRstEmphasisFixture(
        test_id="multiple_patterns",
        input_text="match django-* or flask-* packages",
        expected="match django-\\* or flask-\\* packages",
    ),
    EscapeRstEmphasisFixture(
        test_id="plain_text",
        input_text="plain text without patterns",
        expected="plain text without patterns",
    ),
    EscapeRstEmphasisFixture(
        test_id="rst_emphasis_unchanged",
        input_text="*emphasis* is ok",
        expected="*emphasis* is ok",
    ),
    EscapeRstEmphasisFixture(
        test_id="already_escaped",
        input_text="django-\\*",
        expected="django-\\*",
    ),
    EscapeRstEmphasisFixture(
        test_id="empty_string",
        input_text="",
        expected="",
    ),
    EscapeRstEmphasisFixture(
        test_id="pattern_at_end",
        input_text="ending with pattern-*",
        expected="ending with pattern-\\*",
    ),
    EscapeRstEmphasisFixture(
        test_id="hyphen_without_asterisk",
        input_text="word-with-hyphens",
        expected="word-with-hyphens",
    ),
    EscapeRstEmphasisFixture(
        test_id="asterisk_without_hyphen",
        input_text="asterisk * alone",
        expected="asterisk * alone",
    ),
    EscapeRstEmphasisFixture(
        test_id="double_asterisk",
        input_text="glob-** pattern",
        expected="glob-** pattern",
    ),
    EscapeRstEmphasisFixture(
        test_id="space_after_asterisk",
        input_text="word-* followed by space",
        expected="word-\\* followed by space",
    ),
]


@pytest.mark.parametrize(
    EscapeRstEmphasisFixture._fields,
    ESCAPE_RST_EMPHASIS_FIXTURES,
    ids=[f.test_id for f in ESCAPE_RST_EMPHASIS_FIXTURES],
)
def test_escape_rst_emphasis(test_id: str, input_text: str, expected: str) -> None:
    """Test RST emphasis escaping for glob patterns."""
    assert escape_rst_emphasis(input_text) == expected
