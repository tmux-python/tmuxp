# -*- coding: utf-8 -*-
"""Exceptions for tmuxp.

tmuxp.exc
~~~~~~~~~

"""

from __future__ import absolute_import, unicode_literals

from ._compat import implements_to_string


class TmuxpException(Exception):

    """Base Exception for Tmuxp Errors."""

    pass


class ConfigError(TmuxpException):

    """Error parsing tmuxp configuration dict."""

    pass


class EmptyConfigException(ConfigError):

    """Configuration is empty."""

    pass


class TmuxpPluginException(TmuxpException):

    """Base Exception for Tmuxp Errors."""

    pass


class BeforeLoadScriptNotExists(OSError):
    def __init__(self, *args, **kwargs):
        super(BeforeLoadScriptNotExists, self).__init__(*args, **kwargs)

        self.strerror = "before_script file '%s' doesn't exist." % self.strerror


@implements_to_string
class BeforeLoadScriptError(Exception):

    """Exception replacing :py:class:`subprocess.CalledProcessError` for
    :meth:`tmuxp.util.run_before_script`.
    """

    def __init__(self, returncode, cmd, output=None):
        self.returncode = returncode
        self.cmd = cmd
        self.output = output
        self.message = (
            'before_script failed with returncode {returncode}.\n'
            'command: {cmd}\n'
            'Error output:\n'
            '{output}'
        ).format(returncode=self.returncode, cmd=self.cmd, output=self.output)

    def __str__(self):
        return self.message
