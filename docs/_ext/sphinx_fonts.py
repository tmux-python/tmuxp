"""Sphinx extension for self-hosted fonts via Fontsource CDN.

Downloads font files at build time, caches them locally, and passes
structured font data to the template context for inline @font-face CSS.
"""

from __future__ import annotations

import logging
import pathlib
import shutil
import typing as t
import urllib.error
import urllib.request

if t.TYPE_CHECKING:
    from sphinx.application import Sphinx

logger = logging.getLogger(__name__)

CDN_TEMPLATE = (
    "https://cdn.jsdelivr.net/npm/{package}@{version}"
    "/files/{font_id}-{subset}-{weight}-{style}.woff2"
)


class SetupDict(t.TypedDict):
    """Return type for Sphinx extension setup()."""

    version: str
    parallel_read_safe: bool
    parallel_write_safe: bool


def _cache_dir() -> pathlib.Path:
    return pathlib.Path.home() / ".cache" / "sphinx-fonts"


def _cdn_url(
    package: str,
    version: str,
    font_id: str,
    subset: str,
    weight: int,
    style: str,
) -> str:
    return CDN_TEMPLATE.format(
        package=package,
        version=version,
        font_id=font_id,
        subset=subset,
        weight=weight,
        style=style,
    )


# Unicode range descriptors per subset — tells the browser to only download
# the file when characters from this range appear on the page.  Ranges are
# from Fontsource / Google Fonts CSS (CSS unicode-range values).
_UNICODE_RANGES: dict[str, str] = {
    "latin": (
        "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6,"
        " U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F,"
        " U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215,"
        " U+FEFF, U+FFFD"
    ),
    "latin-ext": (
        "U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7,"
        " U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF,"
        " U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB,"
        " U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF"
    ),
    "cyrillic": ("U+0301, U+0400-045F, U+0490-0491, U+04B0-04B1, U+2116"),
    "cyrillic-ext": (
        "U+0460-052F, U+1C80-1C8A, U+20B4, U+2DE0-2DFF, U+A640-A69F, U+FE2E-FE2F"
    ),
    "greek": (
        "U+0370-0377, U+037A-037F, U+0384-038A, U+038C, U+038E-03A1, U+03A3-03FF"
    ),
    "vietnamese": (
        "U+0102-0103, U+0110-0111, U+0128-0129, U+0168-0169,"
        " U+01A0-01A1, U+01AF-01B0, U+0300-0301, U+0303-0304,"
        " U+0308-0309, U+0323, U+0329, U+1EA0-1EF9, U+20AB"
    ),
}


def _unicode_range(subset: str) -> str:
    """Return the CSS ``unicode-range`` descriptor for *subset*.

    Falls back to an empty string for unknown subsets (omitting the
    descriptor causes the browser to treat the face as covering all
    codepoints, which is the correct fallback).

    Parameters
    ----------
    subset : str
        Fontsource subset name (e.g. ``"latin"``, ``"latin-ext"``).

    Returns
    -------
    str
        CSS ``unicode-range`` value, or ``""`` if unknown.
    """
    return _UNICODE_RANGES.get(subset, "")


def _download_font(url: str, dest: pathlib.Path) -> bool:
    if dest.exists():
        logger.debug("font cached: %s", dest.name)
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        urllib.request.urlretrieve(url, dest)
        logger.info("downloaded font: %s", dest.name)
    except (urllib.error.URLError, OSError):
        if dest.exists():
            dest.unlink()
        logger.warning("failed to download font: %s", url)
        return False
    return True


def _on_builder_inited(app: Sphinx) -> None:
    if app.builder.format != "html":
        return

    fonts: list[dict[str, t.Any]] = app.config.sphinx_fonts
    variables: dict[str, str] = app.config.sphinx_font_css_variables
    if not fonts:
        return

    cache = _cache_dir()
    static_dir = pathlib.Path(app.outdir) / "_static"
    fonts_dir = static_dir / "fonts"
    fonts_dir.mkdir(parents=True, exist_ok=True)

    font_faces: list[dict[str, str]] = []
    for font in fonts:
        font_id = font["package"].split("/")[-1]
        version = font["version"]
        package = font["package"]
        # Accept "subsets" (list) or legacy "subset" (str).
        subsets: list[str] = font.get("subsets", [font.get("subset", "latin")])
        for subset in subsets:
            for weight in font["weights"]:
                for style in font["styles"]:
                    filename = f"{font_id}-{subset}-{weight}-{style}.woff2"
                    cached = cache / filename
                    url = _cdn_url(package, version, font_id, subset, weight, style)
                    if _download_font(url, cached):
                        shutil.copy2(cached, fonts_dir / filename)
                        font_faces.append(
                            {
                                "family": font["family"],
                                "style": style,
                                "weight": str(weight),
                                "filename": filename,
                                "unicode_range": _unicode_range(subset),
                            }
                        )

    preload_hrefs: list[str] = []
    preload_specs: list[tuple[str, int, str]] = app.config.sphinx_font_preload
    for family_name, weight, style in preload_specs:
        for font in fonts:
            if font["family"] == family_name:
                font_id = font["package"].split("/")[-1]
                # Preload the first (primary) subset only — typically "latin".
                subsets = font.get("subsets", [font.get("subset", "latin")])
                primary = subsets[0] if subsets else "latin"
                filename = f"{font_id}-{primary}-{weight}-{style}.woff2"
                preload_hrefs.append(filename)
                break

    fallbacks: list[dict[str, str]] = app.config.sphinx_font_fallbacks

    app._font_preload_hrefs = preload_hrefs  # type: ignore[attr-defined]
    app._font_faces = font_faces  # type: ignore[attr-defined]
    app._font_fallbacks = fallbacks  # type: ignore[attr-defined]
    app._font_css_variables = variables  # type: ignore[attr-defined]


def _on_html_page_context(
    app: Sphinx,
    pagename: str,
    templatename: str,
    context: dict[str, t.Any],
    doctree: t.Any,
) -> None:
    context["font_preload_hrefs"] = getattr(app, "_font_preload_hrefs", [])
    context["font_faces"] = getattr(app, "_font_faces", [])
    context["font_fallbacks"] = getattr(app, "_font_fallbacks", [])
    context["font_css_variables"] = getattr(app, "_font_css_variables", {})


def setup(app: Sphinx) -> SetupDict:
    """Register config values, events, and return extension metadata."""
    app.add_config_value("sphinx_fonts", [], "html")
    app.add_config_value("sphinx_font_fallbacks", [], "html")
    app.add_config_value("sphinx_font_css_variables", {}, "html")
    app.add_config_value("sphinx_font_preload", [], "html")
    app.connect("builder-inited", _on_builder_inited)
    app.connect("html-page-context", _on_html_page_context)
    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
