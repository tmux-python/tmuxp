# -*- coding: utf8 - *-
"""Exceptions for tmuxp.

tmuxp.exc
~~~~~~~~~

"""

from __future__ import absolute_import, division, print_function, \
    with_statement, unicode_literals


class TmuxpException(Exception):

    """Base Exception for Tmuxp Errors.

    Also for Python 2.6 compat:
        http://stackoverflow.com/a/6029838

    """


class TmuxSessionExists(TmuxpException):

    """Session does not exist in the server."""

    pass


class ConfigError(TmuxpException):

    """Error parsing tmuxp configuration dict."""

    pass


class EmptyConfigException(ConfigError):

    """Configuration is empty."""

    pass
