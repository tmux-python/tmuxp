"""Tests for the build-time mermaid inline-SVG extension (``docs/_ext``)."""

from __future__ import annotations

import importlib.util
import logging
import types
import typing as t
from pathlib import Path

import pytest
from docutils import nodes

# The extension lives under docs/_ext (not an installed package), so load it
# from its file path rather than importing it by name.
_EXT_PATH = (
    Path(__file__).resolve().parent.parent / "docs" / "_ext" / "mermaid_inline.py"
)
_spec = importlib.util.spec_from_file_location("mermaid_inline", _EXT_PATH)
assert _spec is not None
assert _spec.loader is not None
mi = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mi)

# A stand-in for mmdc's real output: fixed ``my-svg`` id, responsive width with
# no height, an inline ``max-width``, an id-scoped style, and a marker ref.
_FAKE_MMDC_SVG = (
    '<svg id="my-svg" width="100%" '
    'style="max-width: 200px; background-color: transparent;" '
    'viewBox="0 0 200 80" role="graphics-document document">'
    "<style>#my-svg{fill:#333;}</style>"
    '<g class="node">a</g>'
    '<path marker-end="url(#my-svg_flowchart-pointEnd)"></path>'
    "</svg>"
)


class NormalizeCase(t.NamedTuple):
    """A ``_normalize_svg`` scenario and its expected substrings."""

    test_id: str
    raw_svg: str
    svg_id: str
    expect_contains: tuple[str, ...]
    expect_absent: tuple[str, ...]


_NORMALIZE_CASES: list[NormalizeCase] = [
    NormalizeCase(
        test_id="width-and-height-from-viewbox",
        raw_svg=(
            '<svg id="my-svg" width="100%" style="max-width: 200px;" '
            'viewBox="0 0 200 80"><style>#my-svg{fill:#333;}</style></svg>'
        ),
        svg_id="mermaid-deadbeef-light",
        expect_contains=(
            'width="200"',
            'height="80"',
            'id="mermaid-deadbeef-light"',
            "#mermaid-deadbeef-light{",
        ),
        expect_absent=("my-svg", "max-width", 'width="100%"'),
    ),
    NormalizeCase(
        test_id="marker-references-rewritten",
        raw_svg=(
            '<svg id="my-svg" width="100%" viewBox="0 0 10 10">'
            '<g marker-end="url(#my-svg_end)"/></svg>'
        ),
        svg_id="mermaid-abc-dark",
        expect_contains=("url(#mermaid-abc-dark_end)", 'width="10"', 'height="10"'),
        expect_absent=("my-svg",),
    ),
    NormalizeCase(
        test_id="decimal-viewbox-dimensions",
        raw_svg=(
            '<svg id="my-svg" width="100%" style="max-width: 1141.25px;" '
            'viewBox="0 0 1141.25 94"></svg>'
        ),
        svg_id="mermaid-x-light",
        expect_contains=('width="1141.25"', 'height="94"'),
        expect_absent=("max-width",),
    ),
]


@pytest.mark.parametrize(
    "case",
    _NORMALIZE_CASES,
    ids=[c.test_id for c in _NORMALIZE_CASES],
)
def test_normalize_svg(case: NormalizeCase) -> None:
    """``_normalize_svg`` rewrites the id, sets size, and drops ``max-width``."""
    out = mi._normalize_svg(case.raw_svg, svg_id=case.svg_id)
    for needle in case.expect_contains:
        assert needle in out, f"{case.test_id}: expected {needle!r}"
    for needle in case.expect_absent:
        assert needle not in out, f"{case.test_id}: unexpected {needle!r}"


class DigestCase(t.NamedTuple):
    """Two ``_diagram_digest`` inputs and whether their hashes should match."""

    test_id: str
    a_source: str
    a_theme: str
    b_source: str
    b_theme: str
    expect_equal: bool


_DIGEST_CASES: list[DigestCase] = [
    DigestCase(
        "identical-inputs-match",
        "flowchart LR a-->b",
        "default",
        "flowchart LR a-->b",
        "default",
        True,
    ),
    DigestCase(
        "theme-differs",
        "flowchart LR a-->b",
        "default",
        "flowchart LR a-->b",
        "dark",
        False,
    ),
    DigestCase(
        "source-differs",
        "flowchart LR a-->b",
        "default",
        "flowchart LR a-->c",
        "default",
        False,
    ),
]


@pytest.mark.parametrize(
    "case",
    _DIGEST_CASES,
    ids=[c.test_id for c in _DIGEST_CASES],
)
def test_diagram_digest(case: DigestCase) -> None:
    """``_diagram_digest`` is stable per input and varies by theme and source."""
    a = mi._diagram_digest(case.a_source, case.a_theme)
    b = mi._diagram_digest(case.b_source, case.b_theme)
    assert (a == b) is case.expect_equal
    assert len(a) == 40


def test_svg_element_id_is_themed_and_unique() -> None:
    """``_svg_element_id`` yields distinct, theme-suffixed ids per variant."""
    digest = mi._diagram_digest("flowchart LR a-->b", "")
    light = mi._svg_element_id(digest, "light")
    dark = mi._svg_element_id(digest, "dark")
    assert light != dark
    assert light.startswith("mermaid-")
    assert light.endswith("-light")


class PaletteCase(t.NamedTuple):
    """A theme name whose furo palette must define the flowchart variables."""

    test_id: str
    theme: str


_PALETTE_CASES: list[PaletteCase] = [
    PaletteCase(test_id=f"{theme}-palette", theme=theme)
    for theme in (mi._THEME_LIGHT, mi._THEME_DARK)
]

_REQUIRED_PALETTE_KEYS = (
    "primaryColor",
    "primaryBorderColor",
    "primaryTextColor",
    "lineColor",
    "textColor",
)


@pytest.mark.parametrize(
    "case",
    _PALETTE_CASES,
    ids=[c.test_id for c in _PALETTE_CASES],
)
def test_palette_defines_flowchart_colors(case: PaletteCase) -> None:
    """Each theme palette defines the mermaid colour variables as hex values."""
    palette = mi._PALETTES[case.theme]
    for key in _REQUIRED_PALETTE_KEYS:
        assert key in palette, f"{case.test_id}: missing {key}"
        assert palette[key].startswith("#"), f"{case.test_id}: {key} not hex"


def _make_translator(tmp_path: Path) -> types.SimpleNamespace:
    """Return a minimal stand-in for the HTML translator the visitor needs."""
    config = types.SimpleNamespace(
        mermaid_inline_cmd="",
        mermaid_inline_puppeteer_config="",
    )
    app = types.SimpleNamespace(confdir=str(tmp_path), config=config)
    builder = types.SimpleNamespace(app=app)
    return types.SimpleNamespace(builder=builder, body=[])


def test_visitor_emits_dual_themed_svg(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The visitor inlines one light and one dark SVG with shared geometry."""
    seen: list[str] = []

    def fake_render_cached(app: object, source: str, theme: str) -> str:
        seen.append(theme)
        return _FAKE_MMDC_SVG

    monkeypatch.setattr(mi, "_render_cached", fake_render_cached)
    translator = _make_translator(tmp_path)
    node = mi.mermaid_inline()
    node["mermaid_source"] = "flowchart LR a-->b"
    node["caption"] = "How it flows"
    node["alt"] = ""

    with pytest.raises(nodes.SkipNode):
        mi.html_visit_mermaid_inline(t.cast("t.Any", translator), node)

    html = "".join(translator.body)
    assert seen == [mi._THEME_LIGHT, mi._THEME_DARK]
    assert html.count("gp-diagram--light") == 1
    assert html.count("gp-diagram--dark") == 1
    assert "<figcaption>How it flows</figcaption>" in html
    assert "my-svg" not in html
    # Both variants normalized to identical geometry -> shift-free toggle.
    assert html.count('viewBox="0 0 200 80"') == 2


def test_visitor_falls_back_when_renderer_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A missing renderer degrades to a text fallback and warns once."""
    monkeypatch.setattr(mi, "_render_warned", False)

    def boom(app: object, source: str, theme: str) -> str:
        msg = "no mmdc"
        raise mi.MermaidRendererMissing(msg)

    monkeypatch.setattr(mi, "_render_cached", boom)
    translator = _make_translator(tmp_path)
    node = mi.mermaid_inline()
    node["mermaid_source"] = "flowchart LR a-->b"
    node["caption"] = ""
    node["alt"] = ""

    with caplog.at_level(logging.WARNING), pytest.raises(nodes.SkipNode):
        mi.html_visit_mermaid_inline(t.cast("t.Any", translator), node)

    html = "".join(translator.body)
    assert 'class="gp-diagram-fallback"' in html
    assert "flowchart LR a--&gt;b" in html
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert any("mermaid render unavailable" in r.getMessage() for r in warnings)


def test_render_cache_is_idempotent(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """``_render_cached`` invokes mmdc once, then serves from the disk cache."""
    calls = {"n": 0}

    def fake_render(app: object, source: str, theme: str) -> str:
        calls["n"] += 1
        return _FAKE_MMDC_SVG

    monkeypatch.setattr(mi, "_render", fake_render)
    config = types.SimpleNamespace(
        mermaid_inline_cmd="",
        mermaid_inline_puppeteer_config="",
    )
    app = types.SimpleNamespace(confdir=str(tmp_path), config=config)

    first = mi._render_cached(t.cast("t.Any", app), "flowchart LR a-->b", "default")
    second = mi._render_cached(t.cast("t.Any", app), "flowchart LR a-->b", "default")

    assert first == second == _FAKE_MMDC_SVG
    assert calls["n"] == 1
    assert list((tmp_path / "_mermaid_cache").glob("*.svg"))


def test_setup_registers_components() -> None:
    """``setup`` registers the node, directive, config values, css, and is safe."""
    recorded: dict[str, list[t.Any]] = {
        "nodes": [],
        "directives": [],
        "config": [],
        "css": [],
    }

    def add_node(node: object, **kwargs: object) -> None:
        recorded["nodes"].append(node)

    def add_directive(name: str, cls: object) -> None:
        recorded["directives"].append((name, cls))

    def add_config_value(name: str, default: object, rebuild: object) -> None:
        recorded["config"].append(name)

    def add_css_file(name: str, **kwargs: object) -> None:
        recorded["css"].append(name)

    app = types.SimpleNamespace(
        add_node=add_node,
        add_directive=add_directive,
        add_config_value=add_config_value,
        add_css_file=add_css_file,
    )
    meta = mi.setup(t.cast("t.Any", app))

    assert meta["parallel_read_safe"] is True
    assert meta["parallel_write_safe"] is True
    assert mi.mermaid_inline in recorded["nodes"]
    assert ("mermaid", mi.MermaidDirective) in recorded["directives"]
    assert "mermaid_inline_cmd" in recorded["config"]
    assert "mermaid_inline_puppeteer_config" in recorded["config"]
    assert "css/gp-diagram.css" in recorded["css"]
