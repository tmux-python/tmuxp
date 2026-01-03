"""Color output utilities for tmuxp CLI.

This module provides semantic color utilities following patterns from vcspull
and CPython's _colorize module. It integrates with the existing style() function
in utils.py for ANSI rendering.

Examples
--------
Basic usage with automatic TTY detection:

>>> colors = Colors()  # AUTO mode by default
>>> # In a TTY, this returns colored text; otherwise plain text

Force colors on or off:

>>> colors = Colors(ColorMode.ALWAYS)
>>> colors.success("loaded")  # doctest: +ELLIPSIS
'...'

>>> colors = Colors(ColorMode.NEVER)
>>> colors.success("loaded")
'loaded'

Environment variables (NO_COLOR, FORCE_COLOR) are respected:

>>> import os
>>> # NO_COLOR takes highest priority
>>> # FORCE_COLOR enables colors even without TTY
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
    >>> "\033[" in result  # Contains ANSI escape
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
