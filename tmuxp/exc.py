# -*- coding: utf-8 -*-
"""Exceptions for tmuxp.

tmuxp.exc
~~~~~~~~~

"""

from __future__ import absolute_import, division, print_function, \
    with_statement, unicode_literals

import subprocess

from ._compat import implements_to_string


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


class BeforeLoadScriptNotExists(OSError):

    def __init__(self, *args, **kwargs):
        super(BeforeLoadScriptNotExists, self).__init__(*args, **kwargs)

        self.strerror = "before_script file '%s' doesn't exist." % self.strerror


@implements_to_string
class BeforeLoadScriptFailed(subprocess.CalledProcessError):

    """Exception extending :py:class:`subprocess.CalledProcessError` for
    :meth:`util.run_before_script`.
    """

    def __init__(self, *args, **kwargs):
        super(BeforeLoadScriptFailed, self).__init__(*args, **kwargs)

    def __str__(self):
        return "before_script failed (%s): %s." \
            "\nError Output: \n%s" % (
                self.returncode, self.cmd, self.output
            )
