"""Sphinx extension for self-hosted fonts via Fontsource CDN.

Downloads font files at build time, caches them locally, and generates
CSS with @font-face declarations and CSS variable overrides.
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
        logger.warning("failed to download font: %s", url)
        return False
    return True


def _generate_css(
    fonts: list[dict[str, t.Any]],
    variables: dict[str, str],
) -> str:
    lines: list[str] = []
    for font in fonts:
        family = font["family"]
        font_id = font["package"].split("/")[-1]
        subset = font.get("subset", "latin")
        for weight in font["weights"]:
            for style in font["styles"]:
                filename = f"{font_id}-{subset}-{weight}-{style}.woff2"
                lines.append("@font-face {")
                lines.append(f'  font-family: "{family}";')
                lines.append(f"  font-style: {style};")
                lines.append(f"  font-weight: {weight};")
                lines.append("  font-display: swap;")
                lines.append(f'  src: url("../fonts/{filename}") format("woff2");')
                lines.append("}")
                lines.append("")

    if variables:
        lines.append(":root {")
        for var, value in variables.items():
            lines.append(f"  {var}: {value};")
        lines.append("}")
        lines.append("")

    return "\n".join(lines)


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
    css_dir = static_dir / "css"
    fonts_dir.mkdir(parents=True, exist_ok=True)
    css_dir.mkdir(parents=True, exist_ok=True)

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

    css_content = _generate_css(fonts, variables)
    (css_dir / "fonts.css").write_text(css_content, encoding="utf-8")
    logger.info("generated fonts.css with %d font families", len(fonts))

    app.add_css_file("css/fonts.css")


def setup(app: Sphinx) -> SetupDict:
    app.add_config_value("sphinx_fonts", [], "html")
    app.add_config_value("sphinx_font_css_variables", {}, "html")
    app.connect("builder-inited", _on_builder_inited)
    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
