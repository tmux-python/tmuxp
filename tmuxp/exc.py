# -*- coding: utf8 - *-
"""Exceptions for tmuxp.

tmuxp.exc
~~~~~~~~~
:copyright: Copyright 2013 Tony Narlock.
:license: BSD, see LICENSE for details

"""


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
