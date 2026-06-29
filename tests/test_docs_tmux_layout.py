"""Tests for the tmux-layout directive (``docs/_ext/tmux_layout.py``)."""

from __future__ import annotations

import importlib.util
import types
import typing as t
from pathlib import Path

import pytest

_EXT_PATH = Path(__file__).resolve().parent.parent / "docs" / "_ext" / "tmux_layout.py"
_spec = importlib.util.spec_from_file_location("tmux_layout", _EXT_PATH)
assert _spec is not None
assert _spec.loader is not None
tl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tl)


class ArrangeCase(t.NamedTuple):
    """A named layout with a pane count and the geometry it should produce."""

    test_id: str
    layout: str
    n: int
    expect_count: int


_ARRANGE_CASES: list[ArrangeCase] = [
    ArrangeCase("even-vertical-3", "even-vertical", 3, 3),
    ArrangeCase("even-horizontal-2", "even-horizontal", 2, 2),
    ArrangeCase("main-vertical-3", "main-vertical", 3, 3),
    ArrangeCase("main-horizontal-3", "main-horizontal", 3, 3),
    ArrangeCase("tiled-4", "tiled", 4, 4),
    ArrangeCase("tiled-3-spans-last-row", "tiled", 3, 3),
    ArrangeCase("single-pane", "even-vertical", 1, 1),
]


@pytest.mark.parametrize(
    "case",
    _ARRANGE_CASES,
    ids=[c.test_id for c in _ARRANGE_CASES],
)
def test_arrange_fills_screen(case: ArrangeCase) -> None:
    """Each arrangement returns the right panes and tiles the screen exactly."""
    width, height = 80, 24
    rects = tl.arrange(case.layout, case.n, width, height)
    assert len(rects) == case.expect_count
    # Non-overlapping panes that fill the screen sum to its area.
    area = sum(r.w * r.h for r in rects)
    assert area == pytest.approx(width * height)
    # Every pane stays within the screen.
    for r in rects:
        assert r.x >= -1e-6
        assert r.y >= -1e-6
        assert r.x + r.w <= width + 1e-6
        assert r.y + r.h <= height + 1e-6


def test_arrange_unknown_layout_raises() -> None:
    """An unknown layout name is a clear error."""
    with pytest.raises(tl.TmuxLayoutError, match="unknown layout"):
        tl.arrange("spiral", 2, 80, 24)


class HighlightCase(t.NamedTuple):
    """A shell command and the Pygments class its first token should carry."""

    test_id: str
    command: str
    expect_class: str


_HIGHLIGHT_CASES: list[HighlightCase] = [
    HighlightCase("single-quoted-string", "echo 'hi there'", 'class="s1"'),
    HighlightCase("comment", "# a note", 'class="c1"'),
]


@pytest.mark.parametrize(
    "case",
    _HIGHLIGHT_CASES,
    ids=[c.test_id for c in _HIGHLIGHT_CASES],
)
def test_highlight_emits_pygments_classes(case: HighlightCase) -> None:
    """``_highlight`` wraps shell tokens in Pygments-classed tspans."""
    out = tl._highlight(case.command)
    assert case.expect_class in out
    assert "<tspan" in out


def test_highlight_leaves_command_builtin_default() -> None:
    """A command builtin (echo/pwd) is left in the default colour, no nb class."""
    assert 'class="nb"' not in tl._highlight("echo hello")
    assert 'class="nb"' not in tl._highlight("pwd")


def test_highlight_escapes_markup() -> None:
    """Angle brackets in a command are HTML-escaped, not emitted as tags."""
    out = tl._highlight("echo <a>")
    assert "<a>" not in out
    assert "&lt;a&gt;" in out


class SplitCase(t.NamedTuple):
    """Directive content lines and the per-pane command lists they yield."""

    test_id: str
    content: list[str]
    expect: list[list[str]]


_SPLIT_CASES: list[SplitCase] = [
    SplitCase("two-panes", ["echo a", "---", "echo b"], [["echo a"], ["echo b"]]),
    SplitCase(
        "multiline-pane",
        ["echo a", "echo b", "---", "echo c"],
        [["echo a", "echo b"], ["echo c"]],
    ),
    SplitCase(
        "blank-lines-dropped", ["echo a", "", "---", "echo b"], [["echo a"], ["echo b"]]
    ),
]


@pytest.mark.parametrize(
    "case",
    _SPLIT_CASES,
    ids=[c.test_id for c in _SPLIT_CASES],
)
def test_split_panes(case: SplitCase) -> None:
    """``_split_panes`` splits on ``---`` and keeps each pane's commands."""
    assert tl._split_panes(case.content) == case.expect


class SizeCase(t.NamedTuple):
    """A ``:size:`` string and the (cols, rows) it parses to."""

    test_id: str
    size: str
    expect: tuple[int, int]


_SIZE_CASES: list[SizeCase] = [
    SizeCase("plain", "64x18", (64, 18)),
    SizeCase("uppercase-x", "80X24", (80, 24)),
]


@pytest.mark.parametrize(
    "case",
    _SIZE_CASES,
    ids=[c.test_id for c in _SIZE_CASES],
)
def test_parse_size(case: SizeCase) -> None:
    """``_parse_size`` reads a ``WxH`` screen size."""
    assert tl._parse_size(case.size) == case.expect


def test_parse_size_invalid_raises() -> None:
    """A malformed size is a clear error."""
    with pytest.raises(tl.TmuxLayoutError, match="invalid size"):
        tl._parse_size("not-a-size")


def test_render_layout_structure() -> None:
    """The rendered SVG has one window, one rect per pane, and highlighting."""
    svg = tl.render_layout([["echo a"], ["echo b"]], "even-vertical", (40, 12))
    assert svg.startswith("<svg")
    assert 'class="gp-tmux-layout"' in svg
    assert svg.count('class="window"') == 1
    assert svg.count('class="pane"') == 2
    assert 'class="gp"' in svg  # the prompt span on each line
    assert svg.endswith("</svg>")


def test_setup_registers_components() -> None:
    """``setup`` registers the node, directive, css, and is parallel-safe."""
    recorded: dict[str, list[t.Any]] = {"nodes": [], "directives": [], "css": []}

    def add_node(node: object, **kwargs: object) -> None:
        recorded["nodes"].append(node)

    def add_directive(name: str, cls: object) -> None:
        recorded["directives"].append((name, cls))

    def add_css_file(name: str, **kwargs: object) -> None:
        recorded["css"].append(name)

    app = types.SimpleNamespace(
        add_node=add_node,
        add_directive=add_directive,
        add_css_file=add_css_file,
    )
    meta = tl.setup(t.cast("t.Any", app))

    assert meta["parallel_read_safe"] is True
    assert meta["parallel_write_safe"] is True
    assert tl.tmux_layout in recorded["nodes"]
    assert ("tmux-layout", tl.TmuxLayoutDirective) in recorded["directives"]
    assert "css/gp-tmux-layout.css" in recorded["css"]
