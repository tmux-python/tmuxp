#!/usr/bin/env python
"""Log utilities for tmuxp."""
import logging
import time
import typing as t

from colorama import Fore, Style

LEVEL_COLORS = {
    "DEBUG": Fore.BLUE,  # Blue
    "INFO": Fore.GREEN,  # Green
    "WARNING": Fore.YELLOW,
    "ERROR": Fore.RED,
    "CRITICAL": Fore.RED,
}

LOG_LEVELS = {
    "CRITICAL": 50,
    "ERROR": 40,
    "WARNING": 30,
    "INFO": 20,
    "DEBUG": 10,
    "NOTSET": 0,
}


def setup_logger(
    logger: t.Optional[logging.Logger] = None,
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
        logger = logging.getLogger()

    if not logger.handlers:  # setup logger handlers
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
        :py:class:`logging.LogRecord` :
            object. this is passed in from inside the
            :py:meth:`logging.Formatter.format` record.

        Returns
        -------
        str
            template for logger message
        """
        reset = Style.RESET_ALL
        levelname = set_style(
            "(%(levelname)s)",
            stylized,
            style_before=(LEVEL_COLORS.get(record.levelname, "") + Style.BRIGHT),
            style_after=Style.RESET_ALL,
            suffix=" ",
        )
        asctime = set_style(
            "%(asctime)s",
            stylized,
            style_before=(Fore.BLACK + Style.DIM + Style.BRIGHT),
            style_after=(Fore.RESET + Style.RESET_ALL),
            prefix="[",
            suffix="]",
        )
        name = set_style(
            "%(name)s",
            stylized,
            style_before=(Fore.WHITE + Style.DIM + Style.BRIGHT),
            style_after=(Fore.RESET + Style.RESET_ALL),
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

        date_format = "%H:%m:%S"
        formatting = self.converter(record.created)
        record.asctime = time.strftime(date_format, formatting)

        prefix = self.template(record) % record.__dict__

        parts = prefix.split(record.message)
        formatted = prefix + " " + record.message
        return formatted.replace("\n", "\n" + parts[0] + " ")


def debug_log_template(
    self: t.Type[logging.Formatter],
    record: logging.LogRecord,
    stylized: t.Optional[bool] = False,
    **kwargs: t.Any,
) -> str:
    """
    Return the prefix for the log message. Template for Formatter.

    Parameters
    ----------
    record :  :py:class:`logging.LogRecord`
        This is passed in from inside the :py:meth:`logging.Formatter.format`
        record.

    Returns
    -------
    str
        Log template.
    """
    reset = Style.RESET_ALL
    levelname = (
        LEVEL_COLORS.get(record.levelname, "")
        + Style.BRIGHT
        + "(%(levelname)1.1s)"
        + Style.RESET_ALL
        + " "
    )
    asctime = (
        "["
        + Fore.BLACK
        + Style.DIM
        + Style.BRIGHT
        + "%(asctime)s"
        + Fore.RESET
        + Style.RESET_ALL
        + "]"
    )
    name = (
        " "
        + Fore.WHITE
        + Style.DIM
        + Style.BRIGHT
        + "%(name)s"
        + Fore.RESET
        + Style.RESET_ALL
        + " "
    )
    module_funcName = Fore.GREEN + Style.BRIGHT + "%(module)s.%(funcName)s()"
    lineno = (
        Fore.BLACK
        + Style.DIM
        + Style.BRIGHT
        + ":"
        + Style.RESET_ALL
        + Fore.CYAN
        + "%(lineno)d"
    )

    tpl = reset + levelname + asctime + name + module_funcName + lineno + reset

    return tpl


class DebugLogFormatter(LogFormatter):
    """Provides greater technical details than standard log Formatter."""

    template = debug_log_template
