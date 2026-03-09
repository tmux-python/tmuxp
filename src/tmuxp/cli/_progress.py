"""Progress indicators for tmuxp CLI.

This module provides a threaded spinner for long-running operations,
using only standard library and ANSI escape sequences.
"""

from __future__ import annotations

import atexit
import collections
import dataclasses
import itertools
import logging
import shutil
import sys
import threading
import time
import typing as t

from ._colors import ANSI_SEQ_RE, ColorMode, Colors, strip_ansi

logger = logging.getLogger(__name__)


if t.TYPE_CHECKING:
    import types


# ANSI Escape Sequences
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
ERASE_LINE = "\033[2K"
CURSOR_TO_COL0 = "\r"
CURSOR_UP_1 = "\x1b[1A"
SYNC_START = "\x1b[?2026h"  # synchronized output: buffer until SYNC_END
SYNC_END = "\x1b[?2026l"  # flush — prevents multi-line flicker

# Spinner frames (braille pattern)
SPINNER_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

BAR_WIDTH = 10  # inner fill character count
DEFAULT_OUTPUT_LINES = 3  # default spinner panel height (lines of script output)


def _visible_len(s: str) -> int:
    r"""Return visible length of *s*, ignoring ANSI escapes.

    Examples
    --------
    >>> _visible_len("hello")
    5
    >>> _visible_len("\033[32mgreen\033[0m")
    5
    >>> _visible_len("")
    0
    """
    return len(strip_ansi(s))


def _truncate_visible(text: str, max_visible: int, suffix: str = "...") -> str:
    r"""Truncate *text* to *max_visible* visible characters, preserving ANSI sequences.

    If the visible length of *text* is already within *max_visible*, it is
    returned unchanged.  Otherwise the text is cut so that exactly
    *max_visible* visible characters remain, a ``\x1b[0m`` reset is appended
    (to prevent color bleed), followed by *suffix*.

    Parameters
    ----------
    text : str
        Input string, possibly containing ANSI escape sequences.
    max_visible : int
        Maximum number of visible (non-ANSI) characters to keep.
    suffix : str
        Appended after the reset when truncation occurs.  Default ``"..."``.

    Returns
    -------
    str
        Truncated string with ANSI sequences intact.

    Examples
    --------
    Plain text truncation:

    >>> _truncate_visible("hello world", 5)
    'hello\x1b[0m...'

    ANSI sequences are preserved whole:

    >>> _truncate_visible("\033[32mgreen\033[0m", 3)
    '\x1b[32mgre\x1b[0m...'

    No truncation needed:

    >>> _truncate_visible("short", 10)
    'short'

    Empty string:

    >>> _truncate_visible("", 5)
    ''
    """
    if max_visible <= 0:
        return ""
    if _visible_len(text) <= max_visible:
        return text

    result: list[str] = []
    visible = 0
    i = 0
    while i < len(text) and visible < max_visible:
        m = ANSI_SEQ_RE.match(text, i)
        if m:
            result.append(m.group())
            i = m.end()
        else:
            result.append(text[i])
            visible += 1
            i += 1
    return "".join(result) + "\x1b[0m" + suffix


SUCCESS_TEMPLATE = "Loaded workspace: {session} ({workspace_path}) {summary}"

PROGRESS_PRESETS: dict[str, str] = {
    "default": "Loading workspace: {session} {bar} {progress} {window}",
    "minimal": "Loading workspace: {session} [{window_progress}]",
    "window": "Loading workspace: {session} {window_bar} {window_progress_rel}",
    "pane": "Loading workspace: {session} {pane_bar} {session_pane_progress}",
    "verbose": (
        "Loading workspace: {session} [window {window_index} of {window_total}"
        " · pane {pane_index} of {pane_total}] {window}"
    ),
}


def render_bar(done: int, total: int, width: int = BAR_WIDTH) -> str:
    """Render a plain-text ASCII progress bar without color.

    Parameters
    ----------
    done : int
        Completed units.
    total : int
        Total units. When ``<= 0``, returns ``""``.
    width : int
        Inner fill character count; default :data:`BAR_WIDTH`.

    Returns
    -------
    str
        A bar like ``"█████░░░░░"``.
        Returns ``""`` when *total* <= 0 or *width* <= 0.

    Examples
    --------
    >>> render_bar(0, 10)
    '░░░░░░░░░░'
    >>> render_bar(5, 10)
    '█████░░░░░'
    >>> render_bar(10, 10)
    '██████████'
    >>> render_bar(0, 0)
    ''
    >>> render_bar(3, 10, width=5)
    '█░░░░'
    """
    if total <= 0 or width <= 0:
        return ""
    filled = min(width, int(done / total * width))
    return "█" * filled + "░" * (width - filled)


class _SafeFormatMap(dict):  # type: ignore[type-arg]
    """dict subclass that returns ``{key}`` for missing keys in format_map."""

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def resolve_progress_format(fmt: str) -> str:
    """Return the format string for *fmt*, resolving preset names.

    If *fmt* is a key in :data:`PROGRESS_PRESETS` the corresponding
    format string is returned; otherwise *fmt* is returned as-is.

    Examples
    --------
    >>> resolve_progress_format("minimal") == PROGRESS_PRESETS["minimal"]
    True
    >>> resolve_progress_format("{session} w{window_progress}")
    '{session} w{window_progress}'
    >>> resolve_progress_format("unknown-preset")
    'unknown-preset'
    """
    return PROGRESS_PRESETS.get(fmt, fmt)


@dataclasses.dataclass
class _WindowStatus:
    """State for a single window in the build tree."""

    name: str
    done: bool = False
    pane_num: int | None = None
    pane_total: int | None = None
    pane_done: int = 0  # panes completed in this window (set on window_done)


class BuildTree:
    """Tracks session/window/pane build state; renders a structural progress tree.

    **Template Token Lifecycle**

    Each token is first available at the event listed in its column.
    ``—`` means the value does not change at that phase.

    .. list-table::
       :header-rows: 1

       * - Token
         - Pre-``session_created``
         - After ``session_created``
         - After ``window_started``
         - After ``pane_creating``
         - After ``window_done``
       * - ``{session}``
         - ``""``
         - session name
         - —
         - —
         - —
       * - ``{window}``
         - ``""``
         - ``""``
         - window name
         - —
         - last window name
       * - ``{window_index}``
         - ``0``
         - ``0``
         - N (1-based started count)
         - —
         - —
       * - ``{window_total}``
         - ``0``
         - total
         - —
         - —
         - —
       * - ``{window_progress}``
         - ``""``
         - ``""``
         - ``"N/M"`` when > 0
         - —
         - —
       * - ``{windows_done}``
         - ``0``
         - ``0``
         - ``0``
         - ``0``
         - increments
       * - ``{windows_remaining}``
         - ``0``
         - total
         - total
         - total
         - decrements
       * - ``{window_progress_rel}``
         - ``""``
         - ``"0/M"``
         - ``"0/M"``
         - —
         - ``"N/M"``
       * - ``{pane_index}``
         - ``0``
         - ``0``
         - ``0``
         - pane_num
         - ``0``
       * - ``{pane_total}``
         - ``0``
         - ``0``
         - window's pane total
         - —
         - window's pane total
       * - ``{pane_progress}``
         - ``""``
         - ``""``
         - ``""``
         - ``"N/M"``
         - ``""``
       * - ``{pane_done}``
         - ``0``
         - ``0``
         - ``0``
         - pane_num
         - pane_total
       * - ``{pane_remaining}``
         - ``0``
         - ``0``
         - pane_total
         - decrements
         - ``0``
       * - ``{pane_progress_rel}``
         - ``""``
         - ``""``
         - ``"0/M"``
         - ``"N/M"``
         - ``"M/M"``
       * - ``{progress}``
         - ``""``
         - ``""``
         - ``"N/M win"``
         - ``"N/M win · P/Q pane"``
         - —
       * - ``{session_pane_total}``
         - ``0``
         - total
         - —
         - —
         - —
       * - ``{session_panes_done}``
         - ``0``
         - ``0``
         - ``0``
         - ``0``
         - accumulated
       * - ``{session_panes_remaining}``
         - ``0``
         - total
         - total
         - total
         - decrements
       * - ``{session_pane_progress}``
         - ``""``
         - ``"0/T"``
         - —
         - —
         - ``"N/T"``
       * - ``{overall_percent}``
         - ``0``
         - ``0``
         - ``0``
         - ``0``
         - updates
       * - ``{summary}``
         - ``""``
         - ``""``
         - ``""``
         - ``""``
         - ``"[N win, M panes]"``
       * - ``{bar}`` (spinner)
         - ``[░░…]``
         - ``[░░…]``
         - starts filling
         - fractional
         - jumps
       * - ``{pane_bar}`` (spinner)
         - ``""``
         - ``[░░…]``
         - —
         - —
         - updates
       * - ``{window_bar}`` (spinner)
         - ``""``
         - ``[░░…]``
         - —
         - —
         - updates
       * - ``{status_icon}`` (spinner)
         - ``""``
         - ``""``
         - ``""``
         - ``""``
         - ``""``

    During ``before_script``: ``{bar}``, ``{pane_bar}``, ``{window_bar}`` show a
    marching animation; ``{status_icon}`` = ``⏸``.

    Examples
    --------
    Empty tree renders nothing:

    >>> from tmuxp.cli._colors import ColorMode, Colors
    >>> colors = Colors(ColorMode.NEVER)
    >>> tree = BuildTree()
    >>> tree.render(colors, 80)
    []

    After session_created event the header appears:

    >>> tree.on_event({"event": "session_created", "name": "my-session"})
    >>> tree.render(colors, 80)
    ['Session']

    After window_started and pane_creating:

    >>> tree.on_event({"event": "window_started", "name": "editor", "pane_total": 2})
    >>> tree.on_event({"event": "pane_creating", "pane_num": 1, "pane_total": 2})
    >>> lines = tree.render(colors, 80)
    >>> lines[1]
    '- editor, pane (1 of 2)'

    After window_done the window gets a checkmark:

    >>> tree.on_event({"event": "window_done"})
    >>> lines = tree.render(colors, 80)
    >>> lines[1]
    '- ✓ editor'

    **Inline status format:**

    >>> tree2 = BuildTree()
    >>> tree2.format_inline("Building projects...")
    'Building projects...'
    >>> tree2.on_event({"event": "session_created", "name": "cihai", "window_total": 3})
    >>> tree2.format_inline("Building projects...")
    'Building projects... cihai'
    >>> tree2.on_event({"event": "window_started", "name": "gp-libs", "pane_total": 2})
    >>> tree2.on_event({"event": "pane_creating", "pane_num": 1, "pane_total": 2})
    >>> tree2.format_inline("Building projects...")
    'Building projects... cihai [1 of 3 windows, 1 of 2 panes] gp-libs'
    """

    def __init__(self, workspace_path: str = "") -> None:
        self.workspace_path: str = workspace_path
        self.session_name: str | None = None
        self.windows: list[_WindowStatus] = []
        self.window_total: int | None = None
        self.session_pane_total: int | None = None
        self.session_panes_done: int = 0
        self.windows_done: int = 0
        self._before_script_event: threading.Event = threading.Event()

    def on_event(self, event: dict[str, t.Any]) -> None:
        """Update tree state from a build event dict.

        Examples
        --------
        >>> tree = BuildTree()
        >>> tree.on_event({
        ...     "event": "session_created", "name": "dev", "window_total": 2,
        ... })
        >>> tree.session_name
        'dev'
        >>> tree.window_total
        2
        >>> tree.on_event({
        ...     "event": "window_started", "name": "editor", "pane_total": 3,
        ... })
        >>> len(tree.windows)
        1
        >>> tree.windows[0].name
        'editor'
        """
        kind = event["event"]
        if kind == "session_created":
            self.session_name = event["name"]
            self.window_total = event.get("window_total")
            self.session_pane_total = event.get("session_pane_total")
        elif kind == "before_script_started":
            self._before_script_event.set()
        elif kind == "before_script_done":
            self._before_script_event.clear()
        elif kind == "window_started":
            self.windows.append(
                _WindowStatus(name=event["name"], pane_total=event["pane_total"])
            )
        elif kind == "pane_creating":
            if self.windows:
                w = self.windows[-1]
                w.pane_num = event["pane_num"]
                w.pane_total = event["pane_total"]
        elif kind == "window_done":
            if self.windows:
                w = self.windows[-1]
                w.done = True
                w.pane_num = None
                w.pane_done = w.pane_total or 0
                self.session_panes_done += w.pane_done
                self.windows_done += 1
        elif kind == "workspace_built":
            for w in self.windows:
                w.done = True

    def render(self, colors: Colors, width: int) -> list[str]:
        """Render the current tree state to a list of display strings.

        Parameters
        ----------
        colors : Colors
            Colors instance for ANSI styling.
        width : int
            Terminal width; window lines are truncated to ``width - 1``.

        Returns
        -------
        list[str]
            Lines to display; empty list if no session has been created yet.
        """
        if self.session_name is None:
            return []
        lines: list[str] = [colors.heading("Session")]
        for w in self.windows:
            if w.done:
                line = f"- {colors.success('✓')} {colors.highlight(w.name)}"
            elif w.pane_num is not None and w.pane_total is not None:
                line = (
                    f"- {colors.highlight(w.name)}"
                    f"{colors.muted(f', pane ({w.pane_num} of {w.pane_total})')}"
                )
            else:
                line = f"- {colors.highlight(w.name)}"
            lines.append(_truncate_visible(line, width - 1, suffix=""))
        return lines

    def _context(self) -> dict[str, t.Any]:
        """Return the current build-state token dict for template rendering.

        Examples
        --------
        Zero-state before any events:

        >>> tree = BuildTree(workspace_path="~/.tmuxp/myapp.yaml")
        >>> ev = {
        ...     "event": "session_created",
        ...     "name": "myapp",
        ...     "window_total": 5,
        ...     "session_pane_total": 10,
        ... }
        >>> tree.on_event(ev)
        >>> ctx = tree._context()
        >>> ctx["workspace_path"]
        '~/.tmuxp/myapp.yaml'
        >>> ctx["session"]
        'myapp'
        >>> ctx["window_total"]
        5
        >>> ctx["window_index"]
        0
        >>> ctx["progress"]
        ''
        >>> ctx["windows_done"]
        0
        >>> ctx["windows_remaining"]
        5
        >>> ctx["window_progress_rel"]
        '0/5'
        >>> ctx["session_pane_total"]
        10
        >>> ctx["session_panes_remaining"]
        10
        >>> ctx["session_pane_progress"]
        '0/10'
        >>> ctx["summary"]
        ''

        After windows complete, summary shows counts:

        >>> tree.on_event({"event": "window_started", "name": "w1", "pane_total": 3})
        >>> tree.on_event({"event": "window_done"})
        >>> tree.on_event({"event": "window_started", "name": "w2", "pane_total": 5})
        >>> tree.on_event({"event": "window_done"})
        >>> tree._context()["summary"]
        '[2 win, 8 panes]'
        """
        w = self.windows[-1] if self.windows else None
        window_idx = len(self.windows)
        win_tot = self.window_total or 0
        pane_idx = (w.pane_num or 0) if w else 0
        pane_tot = (w.pane_total or 0) if w else 0

        win_progress = f"{window_idx}/{win_tot}" if win_tot and window_idx > 0 else ""
        pane_progress = f"{pane_idx}/{pane_tot}" if pane_tot and pane_idx > 0 else ""
        progress_parts = [
            f"{win_progress} win" if win_progress else "",
            f"{pane_progress} pane" if pane_progress else "",
        ]
        progress = " · ".join(p for p in progress_parts if p)

        win_done = self.windows_done
        win_progress_rel = f"{win_done}/{win_tot}" if win_tot else ""

        pane_done_cur = (
            (w.pane_num or 0) if w and not w.done else (w.pane_done if w else 0)
        )
        pane_remaining = max(0, pane_tot - pane_done_cur)
        pane_progress_rel = f"{pane_done_cur}/{pane_tot}" if pane_tot else ""

        spt = self.session_pane_total or 0
        session_pane_progress = f"{self.session_panes_done}/{spt}" if spt else ""
        overall_percent = int(self.session_panes_done / spt * 100) if spt else 0

        summary_parts: list[str] = []
        if self.windows_done:
            summary_parts.append(f"{self.windows_done} win")
        if self.session_panes_done:
            summary_parts.append(f"{self.session_panes_done} panes")
        summary = f"[{', '.join(summary_parts)}]" if summary_parts else ""

        return {
            "workspace_path": self.workspace_path,
            "session": self.session_name or "",
            "window": w.name if w else "",
            "window_index": window_idx,
            "window_total": win_tot,
            "window_progress": win_progress,
            "pane_index": pane_idx,
            "pane_total": pane_tot,
            "pane_progress": pane_progress,
            "progress": progress,
            "windows_done": win_done,
            "windows_remaining": max(0, win_tot - win_done),
            "window_progress_rel": win_progress_rel,
            "pane_done": pane_done_cur,
            "pane_remaining": pane_remaining,
            "pane_progress_rel": pane_progress_rel,
            "session_pane_total": spt,
            "session_panes_done": self.session_panes_done,
            "session_panes_remaining": max(0, spt - self.session_panes_done),
            "session_pane_progress": session_pane_progress,
            "overall_percent": overall_percent,
            "summary": summary,
        }

    def format_template(
        self,
        fmt: str,
        extra: dict[str, t.Any] | None = None,
    ) -> str:
        """Render *fmt* with the current build state.

        Returns ``""`` before ``session_created`` fires so callers can
        fall back to a pre-build message. Unknown ``{tokens}`` are left
        as-is (not dropped silently).

        The optional *extra* dict is merged on top of :meth:`_context` so
        callers (e.g. :class:`Spinner`) can inject ANSI-colored tokens like
        ``{bar}`` without adding color concerns to :class:`BuildTree`.

        Examples
        --------
        >>> tree = BuildTree()
        >>> tree.format_template("{session} [{progress}] {window}")
        ''
        >>> ev = {"event": "session_created", "name": "cihai", "window_total": 3}
        >>> tree.on_event(ev)
        >>> tree.format_template("{session} [{progress}] {window}")
        'cihai [] '
        >>> ev = {"event": "window_started", "name": "editor", "pane_total": 4}
        >>> tree.on_event(ev)
        >>> tree.format_template("{session} [{progress}] {window}")
        'cihai [1/3 win] editor'
        >>> tree.on_event({"event": "pane_creating", "pane_num": 2, "pane_total": 4})
        >>> tree.format_template("{session} [{progress}] {window}")
        'cihai [1/3 win · 2/4 pane] editor'
        >>> tree.format_template("minimal: {session} [{window_progress}]")
        'minimal: cihai [1/3]'
        >>> tree.format_template("{session} {unknown_token}")
        'cihai {unknown_token}'
        >>> tree.format_template("{session}", extra={"custom": "value"})
        'cihai'
        """
        if self.session_name is None:
            return ""
        ctx: dict[str, t.Any] = self._context()
        if extra:
            ctx = {**ctx, **extra}
        return fmt.format_map(_SafeFormatMap(ctx))

    def format_inline(self, base: str) -> str:
        """Return base message with current build state appended inline.

        Parameters
        ----------
        base : str
            The original spinner message to start from.

        Returns
        -------
        str
            ``base`` alone if no session has been created yet; otherwise
            ``"base session_name [W of N windows, P of M panes] window_name"``,
            omitting the bracket section when there is no current window, and
            omitting individual parts when their totals are not known.
        """
        if self.session_name is None:
            return base
        parts = [base, self.session_name]
        if self.windows:
            w = self.windows[-1]
            window_idx = len(self.windows)
            bracket_parts: list[str] = []
            if self.window_total is not None:
                bracket_parts.append(f"{window_idx} of {self.window_total} windows")
            if w.pane_num is not None and w.pane_total is not None:
                bracket_parts.append(f"{w.pane_num} of {w.pane_total} panes")
            if bracket_parts:
                parts.append(f"[{', '.join(bracket_parts)}]")
            parts.append(w.name)
        return " ".join(parts)


class Spinner:
    """A threaded spinner for CLI progress.

    Examples
    --------
    >>> import io
    >>> stream = io.StringIO()
    >>> with Spinner("Build...", color_mode=ColorMode.NEVER, stream=stream) as spinner:
    ...     spinner.add_output_line("Session created: test")
    ...     spinner.update_message("Creating window: editor")
    """

    def __init__(
        self,
        message: str = "Loading...",
        color_mode: ColorMode = ColorMode.AUTO,
        stream: t.TextIO = sys.stderr,
        interval: float = 0.1,
        output_lines: int = DEFAULT_OUTPUT_LINES,
        progress_format: str | None = None,
        workspace_path: str = "",
    ) -> None:
        """Initialize spinner.

        Parameters
        ----------
        message : str
            Text displayed next to the spinner animation.
        color_mode : ColorMode
            ANSI color mode for styled output.
        stream : t.TextIO
            Output stream (default ``sys.stderr``).
        interval : float
            Seconds between animation frames.
        output_lines : int
            Max lines in the scrolling output panel. ``0`` hides the panel,
            ``-1`` means unlimited.
        progress_format : str | None
            Format string for progress output. Tokens are documented in
            :class:`BuildTree`. ``None`` uses the built-in default.
        workspace_path : str
            Absolute path to the workspace config file, shown in success
            output.
        """
        self.message = message
        self._base_message = message
        self.colors = Colors(color_mode)
        self.stream = stream
        self.interval = interval

        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._enabled = self._should_enable()
        self._panel_hidden = output_lines == 0
        if output_lines < 0:
            self._output_lines: collections.deque[str] = (
                collections.deque()
            )  # unlimited
        elif output_lines == 0:
            self._output_lines = collections.deque(maxlen=1)  # drop, never render
        else:
            self._output_lines = collections.deque(maxlen=output_lines)
        self._prev_height: int = 0
        self._build_tree: BuildTree = BuildTree(workspace_path=workspace_path)
        self._progress_format: str | None = (
            resolve_progress_format(progress_format)
            if progress_format is not None
            else None
        )

    def _should_enable(self) -> bool:
        """Check if spinner should be enabled (TTY check)."""
        return self.stream.isatty()

    def _restore_cursor(self) -> None:
        """Unconditionally restore cursor — called by atexit on abnormal exit."""
        self.stream.write(SHOW_CURSOR)
        self.stream.flush()

    def _spin(self) -> None:
        """Spin in background thread."""
        frames = itertools.cycle(SPINNER_FRAMES)
        march_pos = 0  # marching bar position counter (local to _spin)

        self.stream.write(HIDE_CURSOR)
        self.stream.flush()

        try:
            while not self._stop_event.is_set():
                frame = next(frames)
                term_width = shutil.get_terminal_size(fallback=(80, 24)).columns
                if self._panel_hidden:
                    panel: list[str] = []
                else:
                    term_height = shutil.get_terminal_size(
                        fallback=(80, 24),
                    ).lines
                    raw_panel = list(self._output_lines)
                    max_panel = term_height - 2
                    if len(raw_panel) > max_panel:
                        raw_panel = raw_panel[-max_panel:]
                    panel = [
                        _truncate_visible(line, term_width - 1, suffix="")
                        for line in raw_panel
                    ]
                new_height = len(panel) + 1  # panel lines + spinner line

                parts: list[str] = []

                # Erase previous render (cursor is at end of previous spinner line)
                if self._prev_height > 0:
                    parts.append(f"{CURSOR_TO_COL0}{ERASE_LINE}")
                    parts.extend(
                        f"{CURSOR_UP_1}{ERASE_LINE}"
                        for _ in range(self._prev_height - 1)
                    )

                # Write panel lines (tree lines already constrained by render())
                parts.extend(f"{output_line}\n" for output_line in panel)

                # Determine final spinner message
                if (
                    self._progress_format is not None
                    and self._build_tree._before_script_event.is_set()
                ):
                    # Marching bar: sweep a 2-cell highlight across the bar
                    p = march_pos % max(1, BAR_WIDTH - 1)
                    march_bar = (
                        self.colors.muted("░" * p)
                        + self.colors.warning("░░")
                        + self.colors.muted("░" * max(0, BAR_WIDTH - p - 2))
                    )
                    tree = self._build_tree
                    extra: dict[str, t.Any] = {
                        "session": self.colors.highlight(
                            tree.session_name or "",
                        ),
                        "bar": march_bar,
                        "pane_bar": march_bar,
                        "window_bar": march_bar,
                        "status_icon": self.colors.warning("⏸"),
                    }
                    rendered = self._build_tree.format_template(
                        self._progress_format, extra=extra
                    )
                    msg = rendered if rendered else self._base_message
                    march_pos += 1
                else:
                    msg = self.message
                    march_pos = 0  # reset when not in before_script

                # Write spinner line (no trailing newline — cursor stays here)
                spinner_text = f"{self.colors.info(frame)} {msg}"
                if _visible_len(spinner_text) > term_width - 1:
                    spinner_text = _truncate_visible(spinner_text, term_width - 4)
                parts.append(f"{CURSOR_TO_COL0}{spinner_text}")

                # Wrap entire frame in synchronized output to prevent flicker.
                # Terminals that don't support it safely ignore the sequences.
                self.stream.write(SYNC_START + "".join(parts) + SYNC_END)
                self.stream.flush()
                self._prev_height = new_height
                time.sleep(self.interval)
        finally:
            # Erase the whole block and show cursor
            if self._prev_height > 0:
                self.stream.write(f"{CURSOR_TO_COL0}{ERASE_LINE}")
                for _ in range(self._prev_height - 1):
                    self.stream.write(f"{CURSOR_UP_1}{ERASE_LINE}")
            self.stream.write(SHOW_CURSOR)
            self.stream.flush()
            self._prev_height = 0

    def add_output_line(self, line: str) -> None:
        r"""Append a line to the live output panel (thread-safe via GIL).

        When the spinner is disabled (non-TTY), writes directly to the stream
        so output is not silently swallowed.

        Examples
        --------
        >>> import io
        >>> stream = io.StringIO()
        >>> spinner = Spinner("test", color_mode=ColorMode.NEVER, stream=stream)
        >>> spinner.add_output_line("hello world")
        >>> stream.getvalue()
        'hello world\n'
        """
        stripped = line.rstrip("\n\r")
        if stripped:
            if self._enabled:
                self._output_lines.append(stripped)
            else:
                self.stream.write(stripped + "\n")
                self.stream.flush()

    def update_message(self, message: str) -> None:
        """Update the message displayed next to the spinner.

        Examples
        --------
        >>> import io
        >>> stream = io.StringIO()
        >>> spinner = Spinner("initial", color_mode=ColorMode.NEVER, stream=stream)
        >>> spinner.message
        'initial'
        >>> spinner.update_message("updated")
        >>> spinner.message
        'updated'
        """
        self.message = message

    def _build_extra(self) -> dict[str, t.Any]:
        """Return spinner-owned template tokens (colored bar, status_icon).

        These are separated from :meth:`BuildTree._context` to keep ANSI/color
        concerns out of :class:`BuildTree`, which is also used in tests without
        colors.

        Examples
        --------
        >>> import io
        >>> stream = io.StringIO()
        >>> spinner = Spinner("x", color_mode=ColorMode.NEVER, stream=stream)
        >>> spinner._build_tree.on_event(
        ...     {
        ...         "event": "session_created",
        ...         "name": "s",
        ...         "window_total": 4,
        ...         "session_pane_total": 8,
        ...     }
        ... )
        >>> extra = spinner._build_extra()
        >>> extra["bar"]
        '░░░░░░░░░░'
        >>> extra["status_icon"]
        ''
        """
        tree = self._build_tree
        win_tot = tree.window_total or 0
        spt = tree.session_pane_total or 0

        # Composite fraction: (windows_done + pane_frac) / window_total
        if win_tot > 0:
            cw = tree.windows[-1] if tree.windows else None
            pane_frac = 0.0
            if cw and not cw.done and cw.pane_total:
                pane_frac = (cw.pane_num or 0) / cw.pane_total
            composite_done = tree.windows_done + pane_frac
            composite_bar = render_bar(int(composite_done * 100), win_tot * 100)
        else:
            composite_bar = render_bar(0, 0)

        pane_bar = render_bar(tree.session_panes_done, spt)
        window_bar = render_bar(tree.windows_done, win_tot)

        def _color_bar(plain: str) -> str:
            if not plain:
                return plain
            filled = plain.count("█")
            empty = plain.count("░")
            return self.colors.success("█" * filled) + self.colors.muted("░" * empty)

        return {
            "session": self.colors.highlight(tree.session_name or ""),
            "bar": _color_bar(composite_bar),
            "pane_bar": _color_bar(pane_bar),
            "window_bar": _color_bar(window_bar),
            "status_icon": "",
        }

    def on_build_event(self, event: dict[str, t.Any]) -> None:
        """Forward build event to BuildTree and update spinner message inline.

        Examples
        --------
        >>> import io
        >>> stream = io.StringIO()
        >>> spinner = Spinner("Loading", color_mode=ColorMode.NEVER, stream=stream)
        >>> spinner.on_build_event({
        ...     "event": "session_created", "name": "myapp",
        ...     "window_total": 2, "session_pane_total": 3,
        ... })
        >>> spinner._build_tree.session_name
        'myapp'
        """
        self._build_tree.on_event(event)
        if self._progress_format is not None:
            extra = self._build_extra()
            rendered = self._build_tree.format_template(
                self._progress_format, extra=extra
            )
            # Only switch to template output once a window has started so that
            # the session_created → window_started gap doesn't show empty brackets.
            self.message = (
                rendered
                if (rendered and self._build_tree.windows)
                else self._base_message
            )
        else:
            self.message = self._build_tree.format_inline(self._base_message)

    def start(self) -> None:
        """Start the spinner thread.

        Examples
        --------
        >>> import io
        >>> stream = io.StringIO()
        >>> spinner = Spinner("test", color_mode=ColorMode.NEVER, stream=stream)
        >>> spinner.start()
        >>> spinner.stop()
        """
        if not self._enabled:
            return

        atexit.register(self._restore_cursor)
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the spinner thread.

        Examples
        --------
        >>> import io
        >>> stream = io.StringIO()
        >>> spinner = Spinner("test", color_mode=ColorMode.NEVER, stream=stream)
        >>> spinner.start()
        >>> spinner.stop()
        >>> spinner._thread is None
        True
        """
        if self._thread and self._thread.is_alive():
            self._stop_event.set()
            self._thread.join()
        self._thread = None
        atexit.unregister(self._restore_cursor)

    def format_success(self) -> str:
        """Render the success template with current build state.

        Uses :data:`SUCCESS_TEMPLATE` with colored ``{session}``
        (``highlight()``), ``{workspace_path}`` (``info()``), and
        ``{summary}`` (``muted()``) from :meth:`BuildTree._context`.

        Examples
        --------
        >>> import io
        >>> stream = io.StringIO()
        >>> spinner = Spinner("x", color_mode=ColorMode.NEVER, stream=stream,
        ...     workspace_path="~/.tmuxp/myapp.yaml")
        >>> spinner._build_tree.on_event({
        ...     "event": "session_created", "name": "myapp",
        ...     "window_total": 2, "session_pane_total": 4,
        ... })
        >>> spinner._build_tree.on_event(
        ...     {"event": "window_started", "name": "w1", "pane_total": 2})
        >>> spinner._build_tree.on_event({"event": "window_done"})
        >>> spinner._build_tree.on_event(
        ...     {"event": "window_started", "name": "w2", "pane_total": 2})
        >>> spinner._build_tree.on_event({"event": "window_done"})
        >>> spinner.format_success()
        'Loaded workspace: myapp (~/.tmuxp/myapp.yaml) [2 win, 4 panes]'
        """
        tree = self._build_tree
        ctx = tree._context()
        extra: dict[str, t.Any] = {
            "session": self.colors.highlight(tree.session_name or ""),
            "workspace_path": self.colors.info(ctx.get("workspace_path", "")),
            "summary": self.colors.muted(ctx.get("summary", ""))
            if ctx.get("summary")
            else "",
        }
        return SUCCESS_TEMPLATE.format_map(_SafeFormatMap({**ctx, **extra}))

    def success(self, text: str | None = None) -> None:
        """Stop the spinner and print a success line.

        Parameters
        ----------
        text : str | None
            The success message to display after the checkmark.
            When ``None``, uses :meth:`format_success` if a progress format
            is configured, otherwise falls back to ``_base_message``.

        Examples
        --------
        >>> import io
        >>> stream = io.StringIO()
        >>> spinner = Spinner("x", color_mode=ColorMode.NEVER, stream=stream)
        >>> spinner.success("done")
        >>> "✓ done" in stream.getvalue()
        True

        With no args and no progress format, falls back to base message:

        >>> stream2 = io.StringIO()
        >>> spinner2 = Spinner("Loading...", color_mode=ColorMode.NEVER, stream=stream2)
        >>> spinner2.success()
        >>> "✓ Loading..." in stream2.getvalue()
        True
        """
        self.stop()
        if text is None and self._progress_format is not None:
            text = self.format_success()
        elif text is None:
            text = self._base_message
        checkmark = self.colors.success("\u2713")
        msg = f"{checkmark} {text}"
        self.stream.write(f"{msg}\n")
        self.stream.flush()

    def __enter__(self) -> Spinner:
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> t.Literal[False]:
        self.stop()
        return False
