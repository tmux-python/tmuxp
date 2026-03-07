#!/usr/bin/env python
"""Log utilities for tmuxp."""

from __future__ import annotations

import logging
import sys
import time
import typing as t

from tmuxp._internal.colors import _ansi_colors, _ansi_reset_all

logger = logging.getLogger(__name__)

_ANSI_RESET = _ansi_reset_all  # "\033[0m"
_ANSI_BRIGHT = "\033[1m"
_ANSI_FG_RESET = "\033[39m"

LEVEL_COLORS = {
    "DEBUG": f"\033[{_ansi_colors['blue']}m",
    "INFO": f"\033[{_ansi_colors['green']}m",
    "WARNING": f"\033[{_ansi_colors['yellow']}m",
    "ERROR": f"\033[{_ansi_colors['red']}m",
    "CRITICAL": f"\033[{_ansi_colors['red']}m",
}


class TmuxpLoggerAdapter(logging.LoggerAdapter):  # type: ignore[type-arg]
    """LoggerAdapter that merges extra dictionary on Python < 3.13.

    Follows the portable pattern to avoid repeating the same `extra` on every call
    while preserving the ability to add per-call `extra` kwargs.
    """

    def process(
        self, msg: t.Any, kwargs: t.MutableMapping[str, t.Any]
    ) -> tuple[t.Any, t.MutableMapping[str, t.Any]]:
        """Merge extra dictionary on Python < 3.13."""
        extra = dict(self.extra) if self.extra else {}
        if "extra" in kwargs:
            extra.update(kwargs["extra"])
        kwargs["extra"] = extra
        return msg, kwargs


def setup_logger(
    logger: logging.Logger | None = None,
    level: str = "INFO",
) -> None:
    """Configure tmuxp's logging for CLI use.

    Can checks for any existing loggers to prevent loading handlers twice.

    Parameters
    ----------
    logger : :py:class:`Logger`
        logger instance for tmuxp
    """
    if not logger:  # if no logger exists, make one
        logger = logging.getLogger("tmuxp")

    has_handlers = any(not isinstance(h, logging.NullHandler) for h in logger.handlers)

    if not has_handlers:  # setup logger handlers
        channel = logging.StreamHandler()
        formatter = DebugLogFormatter() if level == "DEBUG" else LogFormatter()
        channel.setFormatter(formatter)
        logger.addHandler(channel)

    logger.setLevel(level)


def set_style(
    message: str,
    stylized: bool,
    style_before: str = "",
    style_after: str = "",
    prefix: str = "",
    suffix: str = "",
) -> str:
    """Stylize terminal logging output."""
    if stylized:
        return prefix + style_before + message + style_after + suffix

    return prefix + message + suffix


class LogFormatter(logging.Formatter):
    """Format logs for tmuxp."""

    def template(
        self: logging.Formatter,
        record: logging.LogRecord,
        stylized: bool = False,
        **kwargs: t.Any,
    ) -> str:
        """
        Return the prefix for the log message. Template for Formatter.

        Parameters
        ----------
        record : :py:class:`logging.LogRecord`
            Object passed from :py:meth:`logging.Formatter.format`.

        Returns
        -------
        str
            Template for logger message.
        """
        reset = _ANSI_RESET
        levelname = set_style(
            "(%(levelname)s)",
            stylized,
            style_before=(LEVEL_COLORS.get(record.levelname, "") + _ANSI_BRIGHT),
            style_after=_ANSI_RESET,
            suffix=" ",
        )
        asctime = set_style(
            "%(asctime)s",
            stylized,
            style_before=(f"\033[{_ansi_colors['black']}m" + _ANSI_BRIGHT),
            style_after=(_ANSI_FG_RESET + _ANSI_RESET),
            prefix="[",
            suffix="]",
        )
        name = set_style(
            "%(name)s",
            stylized,
            style_before=(f"\033[{_ansi_colors['white']}m" + _ANSI_BRIGHT),
            style_after=(_ANSI_FG_RESET + _ANSI_RESET),
            prefix=" ",
            suffix=" ",
        )

        if stylized:
            return reset + levelname + asctime + name + reset

        return levelname + asctime + name

    def __init__(self, color: bool = True, **kwargs: t.Any) -> None:
        logging.Formatter.__init__(self, **kwargs)

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record."""
        try:
            record.message = record.getMessage()
        except Exception as e:
            record.message = f"Bad message ({e!r}): {record.__dict__!r}"

        date_format = "%H:%M:%S"
        formatting = self.converter(record.created)
        record.asctime = time.strftime(date_format, formatting)

        prefix = self.template(record) % record.__dict__

        parts = prefix.split(record.message)
        formatted = prefix + " " + record.message
        return formatted.replace("\n", "\n" + parts[0] + " ")


def debug_log_template(
    self: type[logging.Formatter],
    record: logging.LogRecord,
    stylized: bool | None = False,
    **kwargs: t.Any,
) -> str:
    """
    Return the prefix for the log message. Template for Formatter.

    Parameters
    ----------
    record : :py:class:`logging.LogRecord`
        Object passed from :py:meth:`logging.Formatter.format`.

    Returns
    -------
    str
        Log template.
    """
    reset = _ANSI_RESET
    levelname = (
        LEVEL_COLORS.get(record.levelname, "")
        + _ANSI_BRIGHT
        + "(%(levelname)1.1s)"
        + _ANSI_RESET
        + " "
    )
    asctime = (
        "["
        + f"\033[{_ansi_colors['black']}m"
        + _ANSI_BRIGHT
        + "%(asctime)s"
        + _ANSI_FG_RESET
        + _ANSI_RESET
        + "]"
    )
    name = (
        " "
        + f"\033[{_ansi_colors['white']}m"
        + _ANSI_BRIGHT
        + "%(name)s"
        + _ANSI_FG_RESET
        + _ANSI_RESET
        + " "
    )
    module_funcName = (
        f"\033[{_ansi_colors['green']}m" + _ANSI_BRIGHT + "%(module)s.%(funcName)s()"
    )
    lineno = (
        f"\033[{_ansi_colors['black']}m"
        + _ANSI_BRIGHT
        + ":"
        + _ANSI_RESET
        + f"\033[{_ansi_colors['cyan']}m"
        + "%(lineno)d"
    )

    return reset + levelname + asctime + name + module_funcName + lineno + reset


class DebugLogFormatter(LogFormatter):
    """Provides greater technical details than standard log Formatter."""

    template = debug_log_template


def setup_log_file(log_file: str, level: str = "INFO") -> None:
    """Attach a file handler to the tmuxp logger.

    Parameters
    ----------
    log_file : str
        Path to the log file.
    level : str
        Log level name (e.g. "DEBUG", "INFO"). Selects formatter.

    Examples
    --------
    >>> import tempfile, os, logging
    >>> f = tempfile.NamedTemporaryFile(suffix=".log", delete=False)
    >>> f.close()
    >>> setup_log_file(f.name, level="INFO")
    >>> tmuxp_logger = logging.getLogger("tmuxp")
    >>> tmuxp_logger.handlers = [
    ...     h for h in tmuxp_logger.handlers if not isinstance(h, logging.FileHandler)
    ... ]
    >>> os.unlink(f.name)
    """
    handler = logging.FileHandler(log_file)
    formatter = DebugLogFormatter() if level.upper() == "DEBUG" else LogFormatter()
    handler.setFormatter(formatter)
    tmuxp_logger = logging.getLogger("tmuxp")
    tmuxp_logger.addHandler(handler)


def tmuxp_echo(
    message: str | None = None,
    file: t.TextIO | None = None,
) -> None:
    """Print user-facing CLI output.

    Parameters
    ----------
    message : str | None
        Message to print. If None, does nothing.
    file : t.TextIO | None
        Output stream. Defaults to sys.stdout.

    Examples
    --------
    >>> tmuxp_echo("Session loaded")
    Session loaded

    >>> tmuxp_echo("Warning message")
    Warning message
    """
    if message is None:
        return
    print(message, file=file or sys.stdout)
