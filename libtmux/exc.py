from __future__ import (absolute_import, division, print_function,
                        unicode_literals, with_statement)


class LibTmuxException(Exception):

    """Base Exception for Tmuxp Errors."""


class TmuxSessionExists(LibTmuxException):

    """Session does not exist in the server."""

    pass
