#!/usr/bin/env python
"""Log utilities for tmuxp.

tmuxp.log
~~~~~~~~~

"""
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


def setup_logger(logger=None, level="INFO"):
    """
    Setup logging for CLI use.

    Tries to do some conditionals to prevent handlers from being added twice.
    Just to be safe.

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
    message, stylized, style_before=None, style_after=None, prefix="", suffix=""
):
    if stylized:
        return prefix + style_before + message + style_after + suffix

    return prefix + message + suffix


def default_log_template(
    self: t.Type[logging.Formatter],
    record: logging.LogRecord,
    stylized: t.Optional[bool] = False,
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


class LogFormatter(logging.Formatter):
    template = default_log_template

    def __init__(self, color=True, *args, **kwargs):
        logging.Formatter.__init__(self, *args, **kwargs)

    def format(self, record):
        try:
            record.message = record.getMessage()
        except Exception as e:
            record.message = f"Bad message ({e!r}): {record.__dict__!r}"

        date_format = "%H:%m:%S"
        record.asctime = time.strftime(date_format, self.converter(record.created))

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
