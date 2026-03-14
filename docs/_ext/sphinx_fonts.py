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
        subset = font.get("subset", "latin")
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
                        }
                    )

    preload_hrefs: list[str] = []
    preload_specs: list[tuple[str, int, str]] = app.config.sphinx_font_preload
    for family_name, weight, style in preload_specs:
        for font in fonts:
            if font["family"] == family_name:
                font_id = font["package"].split("/")[-1]
                subset = font.get("subset", "latin")
                filename = f"{font_id}-{subset}-{weight}-{style}.woff2"
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
