"""Build-time mermaid rendering for Sphinx, producing inline SVG.

Renders fenced ``mermaid`` blocks to inline ``<svg>`` at build time via
``mmdc`` (`@mermaid-js/mermaid-cli`_), so diagrams paint with the page: there is
no client-side mermaid runtime, no asynchronous pop-in, and no layout shift. The
finished SVG ships inside ``.article-container``, so it also rides through
gp-sphinx's SPA navigation as live DOM with zero re-initialisation.

Each diagram is rendered twice — a light and a dark variant — and both are
inlined, toggled by CSS on ``body[data-theme]`` (see ``gp-diagram.css``). Mermaid
bakes literal colours into an id-scoped, ``!important`` ``<style>`` block, so a
single SVG cannot be re-themed by external CSS; shipping both variants is the
zero-JavaScript path that stays correct across theme switches and SPA swaps.

Authoring (``myst_fence_as_directive=["mermaid"]`` routes the plain fence)::

    ```mermaid
    flowchart LR
        a --> b
    ```

.. _`@mermaid-js/mermaid-cli`: https://github.com/mermaid-js/mermaid-cli
"""

from __future__ import annotations

import hashlib
import html
import json
import os
import pathlib
import re
import shutil
import subprocess
import tempfile
import typing as t

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective

if t.TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.writers.html5 import HTML5Translator

logger = logging.getLogger(__name__)

#: Bump to invalidate the on-disk render cache when render arguments change.
_RENDER_VERSION = "mmdc11-furo-svg-v1"

#: Logical names for the two inlined variants (cache key, SVG id, CSS class).
_THEME_LIGHT = "light"
_THEME_DARK = "dark"

#: System font stack matching gp-furo's body font (gp-furo-tokens --font-stack).
_FONT_STACK = (
    "-apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif"
)

#: mermaid ``base``-theme variables mapped to gp-furo's light/dark colour tokens
#: (gp-furo-tokens: light.ts / dark.ts) so diagrams match the site palette.
#: Colour does not affect layout, so both variants share geometry.
_PALETTES: dict[str, dict[str, str]] = {
    _THEME_LIGHT: {
        "primaryColor": "#f8f9fb",
        "primaryBorderColor": "#0a4bff",
        "primaryTextColor": "#000000",
        "lineColor": "#6b6f76",
        "textColor": "#000000",
        "background": "#ffffff",
        "edgeLabelBackground": "#f8f9fb",
        "secondaryColor": "#ffffff",
        "tertiaryColor": "#f8f9fb",
        "fontFamily": _FONT_STACK,
    },
    _THEME_DARK: {
        "primaryColor": "#1a1c1e",
        "primaryBorderColor": "#3d94ff",
        "primaryTextColor": "#cfd0d0",
        "lineColor": "#81868d",
        "textColor": "#cfd0d0",
        "background": "#131416",
        "edgeLabelBackground": "#1a1c1e",
        "secondaryColor": "#131416",
        "tertiaryColor": "#1a1c1e",
        "fontFamily": _FONT_STACK,
    },
}

#: mermaid hardcodes this id on every rendered SVG and scopes its CSS and
#: arrowhead markers to it; it is rewritten per diagram+theme to avoid
#: duplicate-id collisions when both variants are inlined on one page.
_MERMAID_DEFAULT_ID = "my-svg"

_VIEWBOX_RE = re.compile(r'viewBox="0 0 ([\d.]+) ([\d.]+)"')

#: Guards the "renderer missing/failed" warning so it fires once, not per node.
_render_warned = False


class MermaidError(Exception):
    """Base class for build-time mermaid rendering failures."""


class MermaidRendererMissing(MermaidError):
    """``mmdc`` could not be located in the docs toolchain."""


class MermaidRenderError(MermaidError):
    """``mmdc`` ran but failed to produce an SVG."""


class mermaid_inline(nodes.General, nodes.Element):
    """Doctree node carrying mermaid source until the HTML write phase."""


def _diagram_digest(source: str, theme: str, *, version: str = _RENDER_VERSION) -> str:
    """Return a stable content hash that keys the render cache.

    The hash covers the render version, the theme, and the source, so light and
    dark variants cache separately and a render-argument change busts the cache.

    >>> a = _diagram_digest("flowchart LR a-->b", "default")
    >>> a == _diagram_digest("flowchart LR a-->b", "default")
    True
    >>> a != _diagram_digest("flowchart LR a-->b", "dark")
    True
    >>> len(a)
    40
    """
    payload = f"{version}\x00{theme}\x00{source}"
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def _svg_element_id(digest: str, theme: str) -> str:
    """Return a per-diagram, per-theme SVG id replacing mermaid's ``my-svg``.

    >>> _svg_element_id("abcdef1234567890", "light")
    'mermaid-abcdef123456-light'
    """
    return f"mermaid-{digest[:12]}-{theme}"


def _normalize_svg(svg: str, *, svg_id: str) -> str:
    """Make an ``mmdc`` SVG safe to inline: unique id, explicit size, no max-width.

    Three fixes are applied to mermaid's default output:

    1. The hardcoded ``my-svg`` id token — used by the id attribute, the
       id-scoped ``<style>`` rules, and ``url(#my-svg_...)`` marker references —
       is rewritten to ``svg_id`` so two variants never collide on duplicate ids.
    2. The root ``width="100%"`` (mermaid emits no ``height``) is replaced with
       explicit ``width``/``height`` taken from the ``viewBox``, so the browser
       reserves the diagram's box in the first layout pass — before any script.
    3. The inline ``max-width: NNpx`` is stripped; paired with the stylesheet's
       ``max-width: 100%; height: auto`` the diagram scales without reflow.

    >>> svg = (
    ...     '<svg id="my-svg" width="100%" '
    ...     'style="max-width: 120px; background-color: transparent;" '
    ...     'viewBox="0 0 120 40"><style>#my-svg{fill:#333;}</style>'
    ...     '<g marker-end="url(#my-svg_end)"/></svg>'
    ... )
    >>> out = _normalize_svg(svg, svg_id="mermaid-abc-light")
    >>> "my-svg" in out
    False
    >>> 'width="120"' in out and 'height="40"' in out
    True
    >>> "max-width" in out
    False
    >>> 'id="mermaid-abc-light"' in out and "url(#mermaid-abc-light_end)" in out
    True
    """
    svg = svg.replace(_MERMAID_DEFAULT_ID, svg_id)
    match = _VIEWBOX_RE.search(svg)
    if match is not None:
        width, height = match.group(1), match.group(2)
        svg = re.sub(r'(<svg\b[^>]*?)\s+width="[^"]*"', r"\1", svg, count=1)
        svg = re.sub(r"<svg\b", f'<svg width="{width}" height="{height}"', svg, count=1)
    return re.sub(r"\s*max-width:\s*[\d.]+px;?", "", svg, count=1)


class MermaidDirective(SphinxDirective):
    """Stash a mermaid fence's source on a node for the write phase to render."""

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    option_spec: t.ClassVar[dict[str, t.Callable[[str], t.Any]]] = {
        "caption": directives.unchanged,
        "alt": directives.unchanged,
        "name": directives.unchanged,
    }

    def run(self) -> list[nodes.Node]:
        """Return a single :class:`mermaid_inline` node carrying the source."""
        if not self.content:
            warning = self.state.document.reporter.warning(
                "mermaid directive has no content",
                line=self.lineno,
            )
            return [warning]
        node = mermaid_inline()
        node["mermaid_source"] = "\n".join(self.content)
        node["caption"] = self.options.get("caption", "")
        node["alt"] = self.options.get("alt", "")
        self.add_name(node)
        self.set_source_info(node)
        return [node]


def _discover_chrome() -> str | None:
    """Return a Chrome installed by ``puppeteer browsers install``, if any.

    Puppeteer's automatic resolution can miss the cached browser (its cache dir
    is computed relative to the install location); pointing ``executablePath`` at
    the discovered binary sidesteps that. Linux/WSL layout only.
    """
    cache = pathlib.Path.home() / ".cache" / "puppeteer" / "chrome"
    if not cache.is_dir():
        return None
    candidates = sorted(cache.glob("*/chrome-linux64/chrome"))
    return str(candidates[-1]) if candidates else None


def _resolve_mmdc(app: Sphinx) -> list[str] | None:
    """Locate the ``mmdc`` executable: config, then docs-local, then ``PATH``."""
    configured = app.config.mermaid_inline_cmd
    if configured:
        found = shutil.which(configured)
        if found:
            return [found]
        path = pathlib.Path(configured)
        if path.exists():
            return [str(path)]
    local = pathlib.Path(app.confdir) / "node_modules" / ".bin" / "mmdc"
    if local.exists():
        return [str(local)]
    found = shutil.which("mmdc")
    return [found] if found else None


def _puppeteer_config_file(app: Sphinx, tmpdir: pathlib.Path) -> pathlib.Path:
    """Write a puppeteer config (``--no-sandbox`` + resolved Chrome) and return it.

    An explicit ``mermaid_inline_puppeteer_config`` wins; otherwise a minimal
    config is generated, adding ``executablePath`` from
    ``PUPPETEER_EXECUTABLE_PATH`` or a discovered cached Chrome.
    """
    configured = app.config.mermaid_inline_puppeteer_config
    if configured:
        return pathlib.Path(configured)
    data: dict[str, t.Any] = {
        "args": ["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
    }
    executable = os.environ.get("PUPPETEER_EXECUTABLE_PATH") or _discover_chrome()
    if executable:
        data["executablePath"] = executable
    out = tmpdir / "puppeteer.json"
    out.write_text(json.dumps(data), encoding="utf-8")
    return out


def _render(app: Sphinx, source: str, theme: str) -> str:
    """Render ``source`` to an SVG string via ``mmdc`` for the given theme."""
    mmdc = _resolve_mmdc(app)
    if mmdc is None:
        msg = (
            "mmdc (@mermaid-js/mermaid-cli) not found; install it in the docs "
            "toolchain or set the mermaid_inline_cmd config value"
        )
        raise MermaidRendererMissing(msg)
    with tempfile.TemporaryDirectory(prefix="mermaid-inline-") as td:
        tmpdir = pathlib.Path(td)
        in_file = tmpdir / "diagram.mmd"
        out_file = tmpdir / "diagram.svg"
        config_file = tmpdir / "config.json"
        in_file.write_text(source, encoding="utf-8")
        config: dict[str, t.Any] = {
            "theme": "base",
            "themeVariables": _PALETTES[theme],
        }
        config_file.write_text(json.dumps(config), encoding="utf-8")
        argv = [
            *mmdc,
            "-i",
            str(in_file),
            "-o",
            str(out_file),
            "-b",
            "transparent",
            "-c",
            str(config_file),
            "-p",
            str(_puppeteer_config_file(app, tmpdir)),
        ]
        try:
            subprocess.run(
                argv,
                check=True,
                capture_output=True,
                text=True,
                timeout=180,
            )
        except FileNotFoundError as exc:  # mmdc vanished between resolve and run
            raise MermaidRendererMissing(str(exc)) from exc
        except subprocess.SubprocessError as exc:
            stderr = getattr(exc, "stderr", "") or ""
            msg = f"mmdc failed: {exc}\n{stderr}"
            raise MermaidRenderError(msg) from exc
        if not out_file.is_file():
            msg = "mmdc produced no SVG output"
            raise MermaidRenderError(msg)
        return out_file.read_text(encoding="utf-8")


def _render_cached(app: Sphinx, source: str, theme: str) -> str:
    """Return a rendered SVG, reading/writing a content-hashed on-disk cache.

    The cache lives outside ``_build`` (under the confdir) so it survives the
    ``rm -rf docs/_build`` that precedes a full build.
    """
    digest = _diagram_digest(source, theme)
    cache_dir = pathlib.Path(app.confdir) / "_mermaid_cache"
    cache_file = cache_dir / f"{digest}.svg"
    if cache_file.is_file():
        return cache_file.read_text(encoding="utf-8")
    svg = _render(app, source, theme)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(svg, encoding="utf-8")
    return svg


def _warn_render_failure(node: nodes.Node, exc: MermaidError) -> None:
    """Emit a single build warning when rendering is unavailable or fails."""
    global _render_warned
    if _render_warned:
        return
    _render_warned = True
    logger.warning(
        "mermaid render unavailable; emitting diagram source as text: %s",
        exc,
        location=node,
    )


def html_visit_mermaid_inline(self: HTML5Translator, node: mermaid_inline) -> None:
    """Render the diagram and append dual light/dark inline SVG, then skip."""
    source: str = node["mermaid_source"]
    app = self.builder.app
    try:
        light = _render_cached(app, source, _THEME_LIGHT)
        dark = _render_cached(app, source, _THEME_DARK)
    except MermaidError as exc:
        _warn_render_failure(node, exc)
        self.body.append(
            '<pre class="gp-diagram-fallback">' + html.escape(source) + "</pre>",
        )
        raise nodes.SkipNode from None

    digest = _diagram_digest(source, "")
    light = _normalize_svg(light, svg_id=_svg_element_id(digest, _THEME_LIGHT))
    dark = _normalize_svg(dark, svg_id=_svg_element_id(digest, _THEME_DARK))

    caption: str = node.get("caption", "")
    alt = node.get("alt", "") or caption
    aria = f' aria-label="{html.escape(alt, quote=True)}"' if alt else ""
    ids: list[str] = node.get("ids", [])
    fig_id = f' id="{ids[0]}"' if ids else ""

    parts = [
        f'<figure class="gp-diagram-wrapper"{fig_id}>',
        f'<div class="gp-diagram gp-diagram--light" role="img"{aria}>{light}</div>',
        (
            '<div class="gp-diagram gp-diagram--dark" role="img" '
            f'aria-hidden="true">{dark}</div>'
        ),
    ]
    if caption:
        parts.append(f"<figcaption>{html.escape(caption)}</figcaption>")
    parts.append("</figure>")
    self.body.append("".join(parts))
    raise nodes.SkipNode


def _depart_mermaid_inline(self: HTML5Translator, node: mermaid_inline) -> None:
    """No-op; :func:`html_visit_mermaid_inline` raises ``SkipNode``."""


def setup(app: Sphinx) -> dict[str, t.Any]:
    """Register the directive, node, config values, and stylesheet."""
    app.add_node(
        mermaid_inline,
        html=(html_visit_mermaid_inline, _depart_mermaid_inline),
    )
    app.add_directive("mermaid", MermaidDirective)
    app.add_config_value("mermaid_inline_cmd", "", "env")
    app.add_config_value("mermaid_inline_puppeteer_config", "", "env")
    app.add_css_file("css/gp-diagram.css")
    return {
        "version": "0.1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
