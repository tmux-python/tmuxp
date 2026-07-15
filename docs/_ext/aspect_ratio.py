"""Reserve demo image space via aspect-ratio so pages don't shift on load (CLS).

Sphinx's HTML writer renders image ``:width:`` as an inline pixel style, which
overrides the theme's ``height: auto`` and distorts responsive images. Instead
this stamps each demo ``<img>`` with ``width:<W>px; max-width:100%;
aspect-ratio:W/H`` (computed from the source GIF): the gif shows at its real
size, shrinks on a narrow screen, never scales up, and the browser reserves the
correct box before it loads (no layout shift).
"""

from __future__ import annotations

import re
import typing as t
from pathlib import Path

from sphinx.util.images import get_image_size

if t.TYPE_CHECKING:
    from docutils import nodes
    from sphinx.application import Sphinx

_IMG = re.compile(r'<img\b[^>]*?\bsrc="[^"]+?/([^"/]+?\.gif)"[^>]*?/?>')
_STYLE = re.compile(r'style="[^"]*"')
_sizes: dict[str, tuple[int, int]] = {}


def _index_sizes(app: Sphinx) -> None:
    """Map each source GIF's basename to its intrinsic ``(width, height)``.

    A demo command name can collide across ``demos/asciinema`` (the cropped gifs
    the pages embed), ``demos/vhs`` (uncropped source renders), and legacy
    ``_static`` assets. Index the embedded ``asciinema`` gifs last so their real
    cropped size wins the basename regardless of filesystem walk order.
    """
    gifs = sorted(
        Path(app.srcdir).rglob("*.gif"),
        key=lambda p: "/demos/asciinema/" in p.as_posix(),
    )
    for path in gifs:
        size = get_image_size(path)
        if size is not None:
            _sizes[path.name] = size


def _inject(
    app: Sphinx,
    pagename: str,
    templatename: str,
    context: dict[str, t.Any],
    doctree: nodes.document | None,
) -> None:
    """Rewrite demo ``<img>`` tags to carry ``width:100%; aspect-ratio:W/H``."""
    body = context.get("body")
    if not body or "_images/" not in body:
        return

    def repl(match: re.Match[str]) -> str:
        tag, name = match.group(0), match.group(1)
        size = _sizes.get(name)
        if size is None or "aspect-ratio" in tag:
            return tag
        style = f"width:{size[0]}px;max-width:100%;aspect-ratio:{size[0]}/{size[1]}"
        if 'style="' in tag:
            return _STYLE.sub(f'style="{style}"', tag)
        return tag[:-1].rstrip("/") + f' style="{style}" />'

    context["body"] = _IMG.sub(repl, body)


def setup(app: Sphinx) -> dict[str, t.Any]:
    """Register the aspect-ratio injector."""
    app.connect("builder-inited", _index_sizes)
    app.connect("html-page-context", _inject)
    return {"parallel_read_safe": True, "parallel_write_safe": True}
