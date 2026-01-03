"""Color output utilities for tmuxp CLI.

This module provides semantic color utilities following patterns from vcspull
and CPython's _colorize module. It integrates with the existing style() function
in utils.py for ANSI rendering.

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
NO_COLOR takes highest priority. FORCE_COLOR enables colors even without TTY:

>>> import os
"""

from __future__ import annotations

import enum
import os
import sys


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
    INFO = "cyan"  # Information, paths
    HIGHLIGHT = "magenta"  # Important labels, session names
    MUTED = "blue"  # Subdued info, secondary text

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

    def _colorize(self, text: str, fg: str, bold: bool = False) -> str:
        """Apply color using existing style() function.

        Parameters
        ----------
        text : str
            Text to colorize.
        fg : str
            Foreground color name (e.g., "green", "red").
        bold : bool
            Whether to apply bold style. Default is False.

        Returns
        -------
        str
            Colorized text if enabled, plain text otherwise.
        """
        if self._enabled:
            # Lazy import to avoid circular dependency with utils.py
            from .utils import style

            return style(text, fg=fg, bold=bold)
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
        """Format text as muted (blue, never bold).

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
