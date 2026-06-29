"""Render tmux window layouts as inline SVG that looks like a terminal.

A ``tmux-layout`` directive declares a screen size and a tmux layout; the panes
tile the screen with no gaps, exactly the way tmux splits a window. Each pane's
shell commands are drawn top-left in a fixed-width font and syntax-highlighted
with Pygments, so the diagram reads like the real terminal. This is the
spiritual successor to the old ``aafig`` ASCII-art boxes, but tmux-aware.

Authoring — panes are separated by a ``---`` line, each holding that pane's
commands::

    :::{tmux-layout}
    :size: 64x18
    :layout: even-vertical

    echo 'did you know'
    echo 'you can inline'
    ---
    echo 'single commands'
    ---
    echo 'for panes'
    :::

``:layout:`` is one of tmux's arrangements: ``even-vertical`` (default),
``even-horizontal``, ``main-vertical``, ``main-horizontal``, ``tiled``.

Output is a single inline ``<svg>`` whose colours are CSS custom properties
(``gp-tmux-layout.css``), so it paints with the page, adapts to light/dark via
``body[data-theme]`` with no JavaScript and no second render, and rides
gp-sphinx SPA swaps as live DOM — without the headless-browser dependency the
mermaid pipeline needs.
"""

from __future__ import annotations

import html
import typing as t

from docutils import nodes
from pygments.lexers.shell import BashLexer
from pygments.token import STANDARD_TYPES
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective

if t.TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.writers.html5 import HTML5Translator

logger = logging.getLogger(__name__)

#: Pixels per tmux character cell (column width, row height). The viewBox is in
#: these pixels, so at the SVG's intrinsic size one unit is one CSS pixel and
#: the text renders at the page's code font size, like a real code block.
_CW = 8.0
_CH = 17.0
#: Padding (px) between a pane edge and its text.
_PAD = 6.0
#: Approx. font ascent (px) for placing the first baseline below the padding.
_FONT = 12.0
#: Baseline-to-baseline distance (px) for stacked command lines.
_LINE_H = 17.0
#: A simple shell prompt prefixed to each command line. The ``gp`` class is
#: Pygments' Generic.Prompt, so it takes the theme's prompt colour (like the
#: ``$`` in the site's console blocks).
_PROMPT = '<tspan class="gp">❯ </tspan>'  # noqa: RUF001

_LAYOUTS = (
    "even-vertical",
    "even-horizontal",
    "main-vertical",
    "main-horizontal",
    "tiled",
)
_LEXER = BashLexer()


class TmuxLayoutError(ValueError):
    """A tmux-layout directive could not be rendered."""


class Rect(t.NamedTuple):
    """A pane rectangle in character-cell coordinates."""

    x: float
    y: float
    w: float
    h: float


def _even(n: int, w: float, h: float, *, vertical: bool) -> list[Rect]:
    """Split the screen into ``n`` equal panes, filling it completely.

    >>> [round(r.h, 2) for r in _even(2, 80, 24, vertical=True)]
    [12.0, 12.0]
    >>> [round(r.w, 2) for r in _even(2, 80, 24, vertical=False)]
    [40.0, 40.0]
    """
    rects = []
    for i in range(n):
        if vertical:
            y0, y1 = i * h / n, (i + 1) * h / n
            rects.append(Rect(0.0, y0, w, y1 - y0))
        else:
            x0, x1 = i * w / n, (i + 1) * w / n
            rects.append(Rect(x0, 0.0, x1 - x0, h))
    return rects


def _main(
    n: int, w: float, h: float, *, vertical: bool, ratio: float = 0.5
) -> list[Rect]:
    """One main pane plus the rest split evenly beside/below it.

    >>> r = _main(3, 80, 24, vertical=True)
    >>> (round(r[0].w), round(r[1].x), len(r))
    (40, 40, 3)
    """
    if n == 1:
        return [Rect(0.0, 0.0, w, h)]
    if vertical:
        mw = w * ratio
        rects = [Rect(0.0, 0.0, mw, h)]
        rects += [
            Rect(mw + r.x, r.y, r.w, r.h)
            for r in _even(n - 1, w - mw, h, vertical=True)
        ]
    else:
        mh = h * ratio
        rects = [Rect(0.0, 0.0, w, mh)]
        rects += [
            Rect(r.x, mh + r.y, r.w, r.h)
            for r in _even(n - 1, w, h - mh, vertical=False)
        ]
    return rects


def _tiled(n: int, w: float, h: float) -> list[Rect]:
    """Tile ``n`` panes into a grid that fills the screen (tmux ``tiled``).

    >>> len(_tiled(4, 80, 24)), round(_tiled(4, 80, 24)[0].w)
    (4, 40)
    """
    rows = cols = 1
    while rows * cols < n:
        rows += 1
        if rows * cols < n:
            cols += 1
    rects = []
    for i in range(n):
        r, c = divmod(i, cols)
        in_row = cols if r < rows - 1 else n - cols * (rows - 1)
        x0, x1 = c * w / in_row, (c + 1) * w / in_row
        y0, y1 = r * h / rows, (r + 1) * h / rows
        rects.append(Rect(x0, y0, x1 - x0, y1 - y0))
    return rects


def arrange(layout: str, n: int, w: int, h: int) -> list[Rect]:
    """Return ``n`` pane rectangles filling a ``w`` x ``h`` screen.

    >>> [round(r.h) for r in arrange("even-vertical", 3, 80, 24)]
    [8, 8, 8]
    >>> len(arrange("tiled", 4, 80, 24))
    4
    """
    if n < 1:
        msg = "a tmux layout needs at least one pane"
        raise TmuxLayoutError(msg)
    if n == 1:
        return [Rect(0.0, 0.0, float(w), float(h))]
    if layout == "even-vertical":
        return _even(n, w, h, vertical=True)
    if layout == "even-horizontal":
        return _even(n, w, h, vertical=False)
    if layout == "main-vertical":
        return _main(n, w, h, vertical=True)
    if layout == "main-horizontal":
        return _main(n, w, h, vertical=False)
    if layout == "tiled":
        return _tiled(n, w, h)
    msg = f"unknown layout {layout!r}; expected one of {', '.join(_LAYOUTS)}"
    raise TmuxLayoutError(msg)


def _highlight(line: str) -> str:
    """Return a shell command as Pygments-classed ``<tspan>``s.

    The command name (a shell builtin like ``echo``/``pwd``) is left in the
    default text colour, like a freshly typed command; strings, comments, and
    the like keep their Pygments classes.

    >>> 'class="nb"' in _highlight("echo hello")
    False
    >>> 'class="s1"' in _highlight("echo 'hi'")
    True
    >>> "&#x27;hi&#x27;" in _highlight("echo 'hi'")
    True
    """
    spans = []
    for token, value in _LEXER.get_tokens(line):
        text = value.rstrip("\n")
        if not text:
            continue
        css = STANDARD_TYPES.get(token, "")
        if css == "nb":  # command builtins (echo, pwd) keep the default colour
            css = ""
        escaped = html.escape(text)
        spans.append(f'<tspan class="{css}">{escaped}</tspan>' if css else escaped)
    return "".join(spans)


def _parse_size(size: str) -> tuple[int, int]:
    """Parse a ``WxH`` screen size.

    >>> _parse_size("64x18")
    (64, 18)
    """
    try:
        w_str, h_str = size.lower().split("x", 1)
        return int(w_str), int(h_str)
    except ValueError as exc:
        msg = f"invalid size {size!r}; expected WxH (e.g. 80x24)"
        raise TmuxLayoutError(msg) from exc


def render_layout(panes: list[list[str]], layout: str, size: tuple[int, int]) -> str:
    """Render panes (each a list of command lines) to an inline ``<svg>``.

    >>> svg = render_layout([["echo a"], ["echo b"]], "even-vertical", (40, 12))
    >>> svg.startswith("<svg") and svg.count('class="pane"')
    2
    """
    w, h = size
    rects = arrange(layout, len(panes), w, h)
    vb_w, vb_h = w * _CW, h * _CH
    parts = [
        f'<svg class="gp-tmux-layout" viewBox="0 0 {vb_w:g} {vb_h:g}" '
        f'width="{vb_w:g}" height="{vb_h:g}" role="img" '
        'xmlns="http://www.w3.org/2000/svg">',
    ]
    # Pane fills first; the window border and single dividers go on top so a
    # shared edge is one line, not two abutting pane strokes.
    parts.extend(
        f'<rect class="pane" x="{rect.x * _CW:g}" y="{rect.y * _CH:g}" '
        f'width="{rect.w * _CW:g}" height="{rect.h * _CH:g}"/>'
        for rect in rects
    )
    for rect in rects:
        right, bottom = rect.x + rect.w, rect.y + rect.h
        if right < w:  # internal vertical divider
            parts.append(
                f'<line class="divider" x1="{right * _CW:g}" y1="{rect.y * _CH:g}" '
                f'x2="{right * _CW:g}" y2="{bottom * _CH:g}"/>',
            )
        if bottom < h:  # internal horizontal divider
            parts.append(
                f'<line class="divider" x1="{rect.x * _CW:g}" y1="{bottom * _CH:g}" '
                f'x2="{(rect.x + rect.w) * _CW:g}" y2="{bottom * _CH:g}"/>',
            )
    parts.append(
        f'<rect class="window" x="0" y="0" width="{vb_w:g}" height="{vb_h:g}"/>',
    )
    # Pygments colours come from furo's own `.highlight` rules (theme-matched,
    # light/dark) via `fill: currentColor`; a <g> ignores its background.
    parts.append('<g class="highlight">')
    for rect, commands in zip(rects, panes, strict=True):
        tx = rect.x * _CW + _PAD
        baseline = rect.y * _CH + _PAD + _FONT
        for i, line in enumerate(commands):
            body = _highlight(line)
            if not body:
                continue
            ty = baseline + i * _LINE_H
            parts.append(
                f'<text class="cmd" x="{tx:g}" y="{ty:g}" '
                f'xml:space="preserve">{_PROMPT}{body}</text>',
            )
    parts.append("</g></svg>")
    return "".join(parts)


def _split_panes(content: list[str]) -> list[list[str]]:
    """Split directive content on ``---`` lines into per-pane command lists.

    >>> _split_panes(["echo a", "echo b", "---", "echo c"])
    [['echo a', 'echo b'], ['echo c']]
    """
    panes: list[list[str]] = [[]]
    for line in content:
        if line.strip() == "---":
            panes.append([])
        else:
            panes[-1].append(line.rstrip())
    return [
        [line for line in pane if line.strip()]
        for pane in panes
        if any(p.strip() for p in pane)
    ]


class tmux_layout(nodes.General, nodes.Element):
    """Doctree node carrying a rendered tmux-layout SVG."""


class TmuxLayoutDirective(SphinxDirective):
    """Render a declared tmux layout as an inline, terminal-styled SVG."""

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    option_spec: t.ClassVar[dict[str, t.Callable[[str], t.Any]]] = {
        "size": lambda x: x,
        "layout": lambda x: x,
        "caption": lambda x: x,
    }

    def run(self) -> list[nodes.Node]:
        """Return a :class:`tmux_layout` node with the rendered SVG."""
        panes = _split_panes(list(self.content))
        if not panes:
            warning = self.state.document.reporter.warning(
                "tmux-layout directive has no panes",
                line=self.lineno,
            )
            return [warning]
        layout = self.options.get("layout", "even-vertical")
        try:
            svg = render_layout(
                panes, layout, _parse_size(self.options.get("size", "80x24"))
            )
        except TmuxLayoutError as exc:
            logger.warning("invalid tmux layout: %s", exc, location=self.get_location())
            return [
                nodes.literal_block("\n".join(self.content), "\n".join(self.content))
            ]
        node = tmux_layout()
        node["svg"] = svg
        node["caption"] = self.options.get("caption", "")
        return [node]


def html_visit_tmux_layout(self: HTML5Translator, node: tmux_layout) -> None:
    """Append the inline SVG (wrapped in a figure) and skip the node."""
    caption = node.get("caption", "")
    parts = [f'<figure class="gp-tmux-layout-wrapper">{node["svg"]}']
    if caption:
        parts.append(f"<figcaption>{html.escape(caption)}</figcaption>")
    parts.append("</figure>")
    self.body.append("".join(parts))
    raise nodes.SkipNode


def _depart_tmux_layout(self: HTML5Translator, node: tmux_layout) -> None:
    """No-op; :func:`html_visit_tmux_layout` raises ``SkipNode``."""


def setup(app: Sphinx) -> dict[str, t.Any]:
    """Register the directive, node, and stylesheet."""
    app.add_node(tmux_layout, html=(html_visit_tmux_layout, _depart_tmux_layout))
    app.add_directive("tmux-layout", TmuxLayoutDirective)
    app.add_css_file("css/gp-tmux-layout.css")
    return {
        "version": "0.1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
