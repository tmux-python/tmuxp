#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Log utilities for tmuxp.

tmuxp.log
~~~~~~~~~

"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals, with_statement)

import logging
import time

from colorama import Fore, Style

LEVEL_COLORS = {
    'DEBUG': Fore.BLUE,  # Blue
    'INFO': Fore.GREEN,  # Green
    'WARNING': Fore.YELLOW,
    'ERROR': Fore.RED,
    'CRITICAL': Fore.RED
}


def default_log_template(self, record):
    """Return the prefix for the log message. Template for Formatter.

    :param: record: :py:class:`logging.LogRecord` object. this is passed in
    from inside the :py:meth:`logging.Formatter.format` record.

    """

    reset = Style.RESET_ALL
    levelname = (
        LEVEL_COLORS.get(record.levelname) + Style.BRIGHT +
        '(%(levelname)s)' + Style.RESET_ALL + ' '
    )
    asctime = (
        '[' + Fore.BLACK + Style.DIM + Style.BRIGHT +
        '%(asctime)s' + Fore.RESET + Style.RESET_ALL + ']'
    )
    name = (
        ' ' + Fore.WHITE + Style.DIM + Style.BRIGHT +
        '%(name)s' + Fore.RESET + Style.RESET_ALL + ' '
    )

    tpl = reset + levelname + asctime + name + reset

    return tpl


class LogFormatter(logging.Formatter):
    template = default_log_template

    def __init__(self, color=True, *args, **kwargs):
        logging.Formatter.__init__(self, *args, **kwargs)

    def format(self, record):
        try:
            record.message = record.getMessage()
        except Exception as e:
            record.message = "Bad message (%r): %r" % (e, record.__dict__)

        date_format = '%H:%m:%S'
        record.asctime = time.strftime(
            date_format, self.converter(record.created)
        )

        prefix = self.template(record) % record.__dict__

        formatted = prefix + " " + record.message
        return formatted.replace("\n", "\n    ")


def debug_log_template(self, record):
    """ Return the prefix for the log message. Template for Formatter.

    :param: record: :py:class:`logging.LogRecord` object. this is passed in
    from inside the :py:meth:`logging.Formatter.format` record.

    """

    reset = Style.RESET_ALL
    levelname = (
        LEVEL_COLORS.get(record.levelname) + Style.BRIGHT +
        '(%(levelname)1.1s)' + Style.RESET_ALL + ' '
    )
    asctime = (
        '[' + Fore.BLACK + Style.DIM + Style.BRIGHT +
        '%(asctime)s' + Fore.RESET + Style.RESET_ALL + ']'
    )
    name = (
        ' ' + Fore.WHITE + Style.DIM + Style.BRIGHT +
        '%(name)s' + Fore.RESET + Style.RESET_ALL + ' '
    )
    module_funcName = (
        Fore.GREEN + Style.BRIGHT +
        '%(module)s.%(funcName)s()'
    )
    lineno = (
        Fore.BLACK + Style.DIM + Style.BRIGHT + ':' + Style.RESET_ALL +
        Fore.CYAN + '%(lineno)d'
    )

    tpl = reset + levelname + asctime + name + module_funcName + lineno + reset

    return tpl


class DebugLogFormatter(LogFormatter):
    """Provides greater technical details than standard log Formatter."""

    template = debug_log_template
