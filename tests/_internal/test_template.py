"""Tests for the in-house template engine."""

from __future__ import annotations

import typing as t

import pytest

from tmuxp._internal.template import (
    UnresolvedVariableError,
    parse_cli_vars,
    render,
)


class RenderFixture(t.NamedTuple):
    """Fixture for the strict=True render path."""

    test_id: str
    template: str
    variables: dict[str, str]
    expected: str | None
    expected_error: type[Exception] | None = None


RENDER_FIXTURES: list[RenderFixture] = [
    RenderFixture("plain_no_subst", "hello world", {}, "hello world"),
    RenderFixture("braced", "hi ${name}!", {"name": "ada"}, "hi ada!"),
    RenderFixture("default_used", "port=${port:-3000}", {}, "port=3000"),
    RenderFixture(
        "default_overridden",
        "port=${port:-3000}",
        {"port": "4000"},
        "port=4000",
    ),
    RenderFixture(
        "missing_strict",
        "hi ${gone}",
        {},
        None,
        UnresolvedVariableError,
    ),
    RenderFixture("multiple_in_one", "${a}/${b}", {"a": "x", "b": "y"}, "x/y"),
    RenderFixture("default_with_special", "p=${p:-a/b/c}", {}, "p=a/b/c"),
    RenderFixture("name_underscore", "${my_var}", {"my_var": "v"}, "v"),
    RenderFixture("dollar_not_braced", "$bare", {"bare": "v"}, "$bare"),
    RenderFixture("env_like_var", "${HOME}", {"HOME": "/tmp"}, "/tmp"),
    RenderFixture("default_empty", "p=${p:-}", {}, "p="),
    RenderFixture(
        "default_with_dash",
        "x=${x:-a-b-c}",
        {},
        "x=a-b-c",
    ),
]


@pytest.mark.parametrize(
    list(RenderFixture._fields),
    RENDER_FIXTURES,
    ids=[f.test_id for f in RENDER_FIXTURES],
)
def test_render(
    test_id: str,
    template: str,
    variables: dict[str, str],
    expected: str | None,
    expected_error: type[Exception] | None,
) -> None:
    """Run each render fixture; verify output or error."""
    if expected_error is not None:
        with pytest.raises(expected_error):
            render(template, variables)
    else:
        assert render(template, variables) == expected


def test_render_non_strict_leaves_missing_alone() -> None:
    """strict=False keeps unresolved placeholders for later expansion."""
    out = render("untouched ${HOME}", {}, strict=False)
    assert out == "untouched ${HOME}"


def test_render_non_strict_still_substitutes_known() -> None:
    """strict=False resolves what it can and leaves the rest."""
    out = render("${a} ${b}", {"a": "1"}, strict=False)
    assert out == "1 ${b}"


def test_render_default_does_not_apply_when_explicit_none() -> None:
    """``${name}`` (no default) raises in strict; not silent-empty."""
    with pytest.raises(UnresolvedVariableError):
        render("${name}", {})


def test_render_unresolved_error_is_keyerror_subclass() -> None:
    """UnresolvedVariableError is a KeyError subclass."""
    try:
        render("${x}", {})
    except KeyError:
        return
    pytest.fail("Expected KeyError-derived UnresolvedVariableError")


class ParseVarsFixture(t.NamedTuple):
    """Fixture for parse_cli_vars."""

    test_id: str
    args: list[str]
    expected: dict[str, str] | None
    expected_error: type[Exception] | None = None


PARSE_FIXTURES: list[ParseVarsFixture] = [
    ParseVarsFixture("empty", [], {}),
    ParseVarsFixture("single", ["app=blog"], {"app": "blog"}),
    ParseVarsFixture("multiple", ["a=1", "b=2"], {"a": "1", "b": "2"}),
    ParseVarsFixture(
        "value_contains_equals",
        ["url=https://example.com/?a=1"],
        {"url": "https://example.com/?a=1"},
    ),
    ParseVarsFixture("empty_value", ["x="], {"x": ""}),
    ParseVarsFixture("missing_equals", ["nope"], None, ValueError),
]


@pytest.mark.parametrize(
    list(ParseVarsFixture._fields),
    PARSE_FIXTURES,
    ids=[f.test_id for f in PARSE_FIXTURES],
)
def test_parse_cli_vars(
    test_id: str,
    args: list[str],
    expected: dict[str, str] | None,
    expected_error: type[Exception] | None,
) -> None:
    """Round-trip CLI tokens to the variable dict."""
    if expected_error is not None:
        with pytest.raises(expected_error):
            parse_cli_vars(args)
    else:
        assert parse_cli_vars(args) == expected
