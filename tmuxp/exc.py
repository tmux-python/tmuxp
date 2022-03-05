"""Exceptions for tmuxp.

tmuxp.exc
~~~~~~~~~

"""
from ._compat import implements_to_string


class TmuxpException(Exception):

    """Base Exception for Tmuxp Errors."""


class ConfigError(TmuxpException):

    """Error parsing tmuxp configuration dict."""


class EmptyConfigException(ConfigError):

    """Configuration is empty."""


class TmuxpPluginException(TmuxpException):

    """Base Exception for Tmuxp Errors."""


class BeforeLoadScriptNotExists(OSError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
            "before_script failed with returncode {returncode}.\n"
            "command: {cmd}\n"
            "Error output:\n"
            "{output}"
        ).format(returncode=self.returncode, cmd=self.cmd, output=self.output)

    def __str__(self):
        return self.message
