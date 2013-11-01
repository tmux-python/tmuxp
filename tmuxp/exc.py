# -*- coding: utf8 - *-
"""Exceptions for tmuxp.

tmuxp.exc
~~~~~~~~~
:copyright: Copyright 2013 Tony Narlock.
:license: BSD, see LICENSE for details

"""


class TmuxSessionExists(Exception):

    """Session does not exist in the server."""

    pass


class ConfigError(Exception):

    """Error parsing tmuxp configuration dict."""

    pass


class EmptyConfigException(ConfigError):

    """Configuration is empty."""

    pass
