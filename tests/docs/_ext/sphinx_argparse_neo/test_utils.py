"""Tests for sphinx_argparse_neo text processing utilities."""

from __future__ import annotations

import typing as t

import pytest
from sphinx_argparse_neo.utils import strip_ansi

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
