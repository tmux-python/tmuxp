"""Color output utilities for tmuxp CLI.

This module provides semantic color utilities following patterns from vcspull
and CPython's _colorize module. It includes low-level ANSI styling functions
and high-level semantic color utilities.

Examples
--------
Basic usage with automatic TTY detection (AUTO mode is the default).
In a TTY, colored text is returned; otherwise plain text:

>>> colors = Colors()

Force colors on or off:

>>> colors = Colors(ColorMode.ALWAYS)
>>> colors.success("loaded")  # doctest: +ELLIPSIS
'...'

>>> colors = Colors(ColorMode.NEVER)
>>> colors.success("loaded")
'loaded'

Environment variables NO_COLOR and FORCE_COLOR are respected.
NO_COLOR takes highest priority (disables even in ALWAYS mode):

>>> monkeypatch.setenv("NO_COLOR", "1")
>>> colors = Colors(ColorMode.ALWAYS)
>>> colors.success("loaded")
'loaded'

FORCE_COLOR enables colors in AUTO mode even without TTY:

>>> import sys
>>> monkeypatch.delenv("NO_COLOR", raising=False)
>>> monkeypatch.setenv("FORCE_COLOR", "1")
>>> monkeypatch.setattr(sys.stdout, "isatty", lambda: False)
>>> colors = Colors(ColorMode.AUTO)
>>> colors.success("loaded")  # doctest: +ELLIPSIS
'...'
"""

from __future__ import annotations

import enum
import os
import re
import sys
import typing as t

if t.TYPE_CHECKING:
    from typing import TypeAlias

    CLIColour: TypeAlias = int | tuple[int, int, int] | str


class ColorMode(enum.Enum):
    """Color output modes for CLI.

    Examples
    --------
    >>> ColorMode.AUTO.value
    'auto'
    >>> ColorMode.ALWAYS.value
    'always'
    >>> ColorMode.NEVER.value
    'never'
    """

    AUTO = "auto"
    ALWAYS = "always"
    NEVER = "never"


class Colors:
    r"""Semantic color utilities for CLI output.

    Provides semantic color methods (success, warning, error, etc.) that
    conditionally apply ANSI colors based on the color mode and environment.

    Parameters
    ----------
    mode : ColorMode
        Color mode to use. Default is AUTO which detects TTY.

    Attributes
    ----------
    SUCCESS : str
        Color name for success messages (green)
    WARNING : str
        Color name for warning messages (yellow)
    ERROR : str
        Color name for error messages (red)
    INFO : str
        Color name for informational messages (cyan)
    HEADING : str
        Color name for section headers (bright_cyan)
    HIGHLIGHT : str
        Color name for highlighted/important text (magenta)
    MUTED : str
        Color name for subdued/secondary text (blue)

    Examples
    --------
    >>> colors = Colors(ColorMode.NEVER)
    >>> colors.success("session loaded")
    'session loaded'
    >>> colors.error("failed to load")
    'failed to load'

    >>> colors = Colors(ColorMode.ALWAYS)
    >>> result = colors.success("ok")

    Check that result contains ANSI escape codes:

    >>> "\033[" in result
    True
    """

    # Semantic color names (used with style())
    SUCCESS = "green"  # Success, loaded, up-to-date
    WARNING = "yellow"  # Warnings, changes needed
    ERROR = "red"  # Errors, failures
    INFO = "cyan"  # Information, paths, supplementary (L2)
    HEADING = "bright_cyan"  # Section headers (L0) - brighter than INFO
    HIGHLIGHT = "magenta"  # Important labels, session names (L1)
    MUTED = "blue"  # Subdued info, secondary text (L3)

    def __init__(self, mode: ColorMode = ColorMode.AUTO) -> None:
        """Initialize color manager.

        Parameters
        ----------
        mode : ColorMode
            Color mode to use (auto, always, never). Default is AUTO.

        Examples
        --------
        >>> colors = Colors()
        >>> colors.mode
        <ColorMode.AUTO: 'auto'>

        >>> colors = Colors(ColorMode.NEVER)
        >>> colors._enabled
        False
        """
        self.mode = mode
        self._enabled = self._should_enable()

    def _should_enable(self) -> bool:
        """Determine if color should be enabled.

        Follows CPython-style precedence:
        1. NO_COLOR env var (any value) -> disable
        2. ColorMode.NEVER -> disable
        3. ColorMode.ALWAYS -> enable
        4. FORCE_COLOR env var (any value) -> enable
        5. TTY check -> enable if stdout is a terminal

        Returns
        -------
        bool
            True if colors should be enabled.

        Examples
        --------
        >>> colors = Colors(ColorMode.NEVER)
        >>> colors._should_enable()
        False
        """
        # NO_COLOR takes highest priority (standard convention)
        if os.environ.get("NO_COLOR"):
            return False

        if self.mode == ColorMode.NEVER:
            return False
        if self.mode == ColorMode.ALWAYS:
            return True

        # AUTO mode: check FORCE_COLOR then TTY
        if os.environ.get("FORCE_COLOR"):
            return True

        return sys.stdout.isatty()

    def _colorize(
        self, text: str, fg: str, bold: bool = False, dim: bool = False
    ) -> str:
        """Apply color using style() function.

        Parameters
        ----------
        text : str
            Text to colorize.
        fg : str
            Foreground color name (e.g., "green", "red").
        bold : bool
            Whether to apply bold style. Default is False.
        dim : bool
            Whether to apply dim/faint style. Default is False.

        Returns
        -------
        str
            Colorized text if enabled, plain text otherwise.

        Examples
        --------
        When colors are enabled, applies ANSI escape codes:

        >>> colors = Colors(ColorMode.ALWAYS)
        >>> colors._colorize("test", "green")  # doctest: +ELLIPSIS
        '...'

        When colors are disabled, returns plain text:

        >>> colors = Colors(ColorMode.NEVER)
        >>> colors._colorize("test", "green")
        'test'
        """
        if self._enabled:
            return style(text, fg=fg, bold=bold, dim=dim)
        return text

    def success(self, text: str, bold: bool = False) -> str:
        """Format text as success (green).

        Parameters
        ----------
        text : str
            Text to format.
        bold : bool
            Whether to apply bold style. Default is False.

        Returns
        -------
        str
            Formatted text.

        Examples
        --------
        >>> colors = Colors(ColorMode.NEVER)
        >>> colors.success("loaded")
        'loaded'
        """
        return self._colorize(text, self.SUCCESS, bold)

    def warning(self, text: str, bold: bool = False) -> str:
        """Format text as warning (yellow).

        Parameters
        ----------
        text : str
            Text to format.
        bold : bool
            Whether to apply bold style. Default is False.

        Returns
        -------
        str
            Formatted text.

        Examples
        --------
        >>> colors = Colors(ColorMode.NEVER)
        >>> colors.warning("check config")
        'check config'
        """
        return self._colorize(text, self.WARNING, bold)

    def error(self, text: str, bold: bool = False) -> str:
        """Format text as error (red).

        Parameters
        ----------
        text : str
            Text to format.
        bold : bool
            Whether to apply bold style. Default is False.

        Returns
        -------
        str
            Formatted text.

        Examples
        --------
        >>> colors = Colors(ColorMode.NEVER)
        >>> colors.error("failed")
        'failed'
        """
        return self._colorize(text, self.ERROR, bold)

    def info(self, text: str, bold: bool = False) -> str:
        """Format text as info (cyan).

        Parameters
        ----------
        text : str
            Text to format.
        bold : bool
            Whether to apply bold style. Default is False.

        Returns
        -------
        str
            Formatted text.

        Examples
        --------
        >>> colors = Colors(ColorMode.NEVER)
        >>> colors.info("/path/to/config.yaml")
        '/path/to/config.yaml'
        """
        return self._colorize(text, self.INFO, bold)

    def highlight(self, text: str, bold: bool = True) -> str:
        """Format text as highlighted (magenta, bold by default).

        Parameters
        ----------
        text : str
            Text to format.
        bold : bool
            Whether to apply bold style. Default is True.

        Returns
        -------
        str
            Formatted text.

        Examples
        --------
        >>> colors = Colors(ColorMode.NEVER)
        >>> colors.highlight("my-session")
        'my-session'
        """
        return self._colorize(text, self.HIGHLIGHT, bold)

    def muted(self, text: str) -> str:
        """Format text as muted (blue).

        Parameters
        ----------
        text : str
            Text to format.

        Returns
        -------
        str
            Formatted text.

        Examples
        --------
        >>> colors = Colors(ColorMode.NEVER)
        >>> colors.muted("(optional)")
        '(optional)'
        """
        return self._colorize(text, self.MUTED, bold=False)

    def heading(self, text: str) -> str:
        """Format text as a section heading (bright cyan, bold).

        Used for section headers like 'Local workspaces:' or 'Global workspaces:'.
        Uses bright_cyan to visually distinguish from info() which uses cyan.

        Parameters
        ----------
        text : str
            Text to format.

        Returns
        -------
        str
            Formatted text.

        Examples
        --------
        >>> colors = Colors(ColorMode.NEVER)
        >>> colors.heading("Local workspaces:")
        'Local workspaces:'
        """
        return self._colorize(text, self.HEADING, bold=True)

    # Formatting helpers for structured output

    def format_label(self, label: str) -> str:
        """Format a label (key in key:value pair).

        Parameters
        ----------
        label : str
            Label text to format.

        Returns
        -------
        str
            Highlighted label text (bold magenta when colors enabled).

        Examples
        --------
        >>> colors = Colors(ColorMode.NEVER)
        >>> colors.format_label("tmux path")
        'tmux path'
        """
        return self.highlight(label, bold=True)

    def format_path(self, path: str) -> str:
        """Format a file path with info color.

        Parameters
        ----------
        path : str
            Path string to format.

        Returns
        -------
        str
            Cyan-colored path when colors enabled.

        Examples
        --------
        >>> colors = Colors(ColorMode.NEVER)
        >>> colors.format_path("/usr/bin/tmux")
        '/usr/bin/tmux'
        """
        return self.info(path)

    def format_version(self, version: str) -> str:
        """Format a version string.

        Parameters
        ----------
        version : str
            Version string to format.

        Returns
        -------
        str
            Cyan-colored version when colors enabled.

        Examples
        --------
        >>> colors = Colors(ColorMode.NEVER)
        >>> colors.format_version("3.2a")
        '3.2a'
        """
        return self.info(version)

    def format_separator(self, length: int = 25) -> str:
        """Format a visual separator line.

        Parameters
        ----------
        length : int
            Length of the separator line. Default is 25.

        Returns
        -------
        str
            Muted (blue) separator line when colors enabled.

        Examples
        --------
        >>> colors = Colors(ColorMode.NEVER)
        >>> colors.format_separator()
        '-------------------------'
        >>> colors.format_separator(10)
        '----------'
        """
        return self.muted("-" * length)

    def format_kv(self, key: str, value: str) -> str:
        """Format key: value pair with syntax highlighting.

        Parameters
        ----------
        key : str
            Key/label to highlight.
        value : str
            Value to display (not colorized, allows caller to format).

        Returns
        -------
        str
            Formatted "key: value" string with highlighted key.

        Examples
        --------
        >>> colors = Colors(ColorMode.NEVER)
        >>> colors.format_kv("tmux version", "3.2a")
        'tmux version: 3.2a'
        """
        return f"{self.format_label(key)}: {value}"

    def format_tmux_option(self, line: str) -> str:
        """Format tmux option line with syntax highlighting.

        Handles tmux show-options output formats:
        - "key value" (space-separated)
        - "key=value" (equals-separated)
        - "key[index] value" (array-indexed options)
        - "key" (empty array options with no value)

        Parameters
        ----------
        line : str
            Option line to format.

        Returns
        -------
        str
            Formatted line with highlighted key and info-colored value.

        Examples
        --------
        >>> colors = Colors(ColorMode.NEVER)
        >>> colors.format_tmux_option("status on")
        'status on'
        >>> colors.format_tmux_option("base-index=1")
        'base-index=1'
        >>> colors.format_tmux_option("pane-colours")
        'pane-colours'
        >>> colors.format_tmux_option('status-format[0] "#[align=left]"')
        'status-format[0] "#[align=left]"'
        """
        # Handle "key value" format (space-separated) - check first since values
        # may contain '=' (e.g., status-format[0] "#[align=left]")
        parts = line.split(None, 1)
        if len(parts) == 2:
            return f"{self.highlight(parts[0], bold=False)} {self.info(parts[1])}"

        # Handle key=value format (only for single-token lines)
        if "=" in line:
            key, val = line.split("=", 1)
            return f"{self.highlight(key, bold=False)}={self.info(val)}"

        # Single word = key with no value (empty array option like pane-colours)
        if len(parts) == 1 and parts[0]:
            return self.highlight(parts[0], bold=False)

        # Empty or unparseable - return as-is
        return line


def get_color_mode(color_arg: str | None = None) -> ColorMode:
    """Convert CLI argument string to ColorMode enum.

    Parameters
    ----------
    color_arg : str | None
        Color mode argument from CLI (auto, always, never).
        None defaults to AUTO.

    Returns
    -------
    ColorMode
        The determined color mode. Invalid values return AUTO.

    Examples
    --------
    >>> get_color_mode(None)
    <ColorMode.AUTO: 'auto'>
    >>> get_color_mode("always")
    <ColorMode.ALWAYS: 'always'>
    >>> get_color_mode("NEVER")
    <ColorMode.NEVER: 'never'>
    >>> get_color_mode("invalid")
    <ColorMode.AUTO: 'auto'>
    """
    if color_arg is None:
        return ColorMode.AUTO

    try:
        return ColorMode(color_arg.lower())
    except ValueError:
        return ColorMode.AUTO


# ANSI styling utilities (originally from click, via utils.py)

_ansi_re = re.compile(r"\033\[[;?0-9]*[a-zA-Z]")


def strip_ansi(value: str) -> str:
    r"""Clear ANSI escape codes from a string value.

    Parameters
    ----------
    value : str
        String potentially containing ANSI escape codes.

    Returns
    -------
    str
        String with ANSI codes removed.

    Examples
    --------
    >>> strip_ansi("\033[32mgreen\033[0m")
    'green'
    >>> strip_ansi("plain text")
    'plain text'
    """
    return _ansi_re.sub("", value)


_ansi_colors = {
    "black": 30,
    "red": 31,
    "green": 32,
    "yellow": 33,
    "blue": 34,
    "magenta": 35,
    "cyan": 36,
    "white": 37,
    "reset": 39,
    "bright_black": 90,
    "bright_red": 91,
    "bright_green": 92,
    "bright_yellow": 93,
    "bright_blue": 94,
    "bright_magenta": 95,
    "bright_cyan": 96,
    "bright_white": 97,
}
_ansi_reset_all = "\033[0m"


def _interpret_color(
    color: int | tuple[int, int, int] | str,
    offset: int = 0,
) -> str:
    """Convert color specification to ANSI escape code number.

    Parameters
    ----------
    color : int | tuple[int, int, int] | str
        Color as 256-color index, RGB tuple, or color name.
    offset : int
        Offset for background colors (10 for bg).

    Returns
    -------
    str
        ANSI escape code parameters.

    Examples
    --------
    Color name returns base ANSI code:

    >>> _interpret_color("red")
    '31'

    256-color index returns extended format:

    >>> _interpret_color(196)
    '38;5;196'

    RGB tuple returns 24-bit format:

    >>> _interpret_color((255, 128, 0))
    '38;2;255;128;0'
    """
    if isinstance(color, int):
        return f"{38 + offset};5;{color:d}"

    if isinstance(color, (tuple, list)):
        if len(color) != 3:
            msg = f"RGB color tuple must have exactly 3 values, got {len(color)}"
            raise ValueError(msg)
        r, g, b = color
        for i, component in enumerate((r, g, b)):
            if not isinstance(component, int):
                msg = (
                    f"RGB values must be integers, "
                    f"got {type(component).__name__} at index {i}"
                )
                raise TypeError(msg)
            if not 0 <= component <= 255:
                msg = f"RGB values must be 0-255, got {component} at index {i}"
                raise ValueError(msg)
        return f"{38 + offset};2;{r:d};{g:d};{b:d}"

    return str(_ansi_colors[color] + offset)


class UnknownStyleColor(Exception):
    """Raised when encountering an unknown terminal style color.

    Examples
    --------
    >>> try:
    ...     raise UnknownStyleColor("invalid_color")
    ... except UnknownStyleColor as e:
    ...     "invalid_color" in str(e)
    True
    """

    def __init__(self, color: CLIColour, *args: object, **kwargs: object) -> None:
        return super().__init__(f"Unknown color {color!r}", *args, **kwargs)


def style(
    text: t.Any,
    fg: CLIColour | None = None,
    bg: CLIColour | None = None,
    bold: bool | None = None,
    dim: bool | None = None,
    underline: bool | None = None,
    overline: bool | None = None,
    italic: bool | None = None,
    blink: bool | None = None,
    reverse: bool | None = None,
    strikethrough: bool | None = None,
    reset: bool = True,
) -> str:
    r"""Apply ANSI styling to text.

    Credit: click.

    Parameters
    ----------
    text : Any
        Text to style (will be converted to str).
    fg : CLIColour | None
        Foreground color (name, 256-index, or RGB tuple).
    bg : CLIColour | None
        Background color.
    bold : bool | None
        Apply bold style.
    dim : bool | None
        Apply dim style.
    underline : bool | None
        Apply underline style.
    overline : bool | None
        Apply overline style.
    italic : bool | None
        Apply italic style.
    blink : bool | None
        Apply blink style.
    reverse : bool | None
        Apply reverse video style.
    strikethrough : bool | None
        Apply strikethrough style.
    reset : bool
        Append reset code at end. Default True.

    Returns
    -------
    str
        Styled text with ANSI escape codes.

    Examples
    --------
    >>> style("hello", fg="green")  # doctest: +ELLIPSIS
    '\x1b[32m...'
    >>> "hello" in style("hello", fg="green")
    True
    """
    if not isinstance(text, str):
        text = str(text)

    bits = []

    if fg or fg == 0:
        try:
            bits.append(f"\033[{_interpret_color(fg)}m")
        except (KeyError, ValueError, TypeError):
            raise UnknownStyleColor(color=fg) from None

    if bg or bg == 0:
        try:
            bits.append(f"\033[{_interpret_color(bg, 10)}m")
        except (KeyError, ValueError, TypeError):
            raise UnknownStyleColor(color=bg) from None

    if bold:
        bits.append("\033[1m")
    if dim:
        bits.append("\033[2m")
    if underline is not None:
        bits.append(f"\033[{4 if underline else 24}m")
    if overline is not None:
        bits.append(f"\033[{53 if overline else 55}m")
    if italic is not None:
        bits.append(f"\033[{3 if italic else 23}m")
    if blink is not None:
        bits.append(f"\033[{5 if blink else 25}m")
    if reverse is not None:
        bits.append(f"\033[{7 if reverse else 27}m")
    if strikethrough is not None:
        bits.append(f"\033[{9 if strikethrough else 29}m")
    bits.append(text)
    if reset:
        bits.append(_ansi_reset_all)
    return "".join(bits)


def unstyle(text: str) -> str:
    r"""Remove ANSI styling information from a string.

    Usually it's not necessary to use this function as tmuxp_echo function will
    automatically remove styling if necessary.

    Credit: click.

    Parameters
    ----------
    text : str
        Text to remove style information from.

    Returns
    -------
    str
        Text with ANSI codes removed.

    Examples
    --------
    >>> unstyle("\033[32mgreen\033[0m")
    'green'
    """
    return strip_ansi(text)


def build_description(
    intro: str,
    example_blocks: t.Sequence[tuple[str | None, t.Sequence[str]]],
) -> str:
    r"""Assemble help text with optional example sections.

    Parameters
    ----------
    intro : str
        The introductory description text.
    example_blocks : sequence of (heading, commands) tuples
        Each tuple contains an optional heading and a sequence of example commands.
        If heading is None, the section is titled "examples:".
        If heading is provided, it becomes the section title (without "examples:").

    Returns
    -------
    str
        Formatted description with examples.

    Examples
    --------
    >>> from tmuxp._internal.colors import build_description
    >>> build_description("My tool.", [(None, ["mytool run"])])
    'My tool.\n\nexamples:\n  mytool run'

    >>> build_description("My tool.", [("sync", ["mytool sync repo"])])
    'My tool.\n\nsync examples:\n  mytool sync repo'

    >>> build_description("", [(None, ["cmd"])])
    'examples:\n  cmd'
    """
    import textwrap

    sections: list[str] = []
    intro_text = textwrap.dedent(intro).strip()
    if intro_text:
        sections.append(intro_text)

    for heading, commands in example_blocks:
        if not commands:
            continue
        title = "examples:" if heading is None else f"{heading} examples:"
        lines = [title]
        lines.extend(f"  {command}" for command in commands)
        sections.append("\n".join(lines))

    return "\n\n".join(sections)
