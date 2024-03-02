"""Exceptions for tmuxp."""

import typing as t

from libtmux._internal.query_list import ObjectDoesNotExist

from ._compat import implements_to_string


class TmuxpException(Exception):
    """Base Exception for Tmuxp Errors."""


class WorkspaceError(TmuxpException):
    """Error parsing tmuxp workspace data."""


class SessionNotFound(TmuxpException):
    """tmux session not found."""

    def __init__(
        self,
        session_target: t.Optional[str] = None,
        *args: object,
        **kwargs: object,
    ) -> None:
        msg = "Session not found"
        if session_target is not None:
            msg += f": {session_target}"
        return super().__init__(msg, *args, **kwargs)


class WindowNotFound(TmuxpException):
    """tmux window not found."""

    def __init__(
        self,
        window_target: t.Optional[str] = None,
        *args: object,
        **kwargs: object,
    ) -> None:
        msg = "Window not found"
        if window_target is not None:
            msg += f": {window_target}"
        return super().__init__(msg, *args, **kwargs)


class PaneNotFound(TmuxpException):
    """tmux pane not found."""

    def __init__(
        self,
        pane_target: t.Optional[str] = None,
        *args: object,
        **kwargs: object,
    ) -> None:
        msg = "Pane not found"
        if pane_target is not None:
            msg += f": {pane_target}"
        return super().__init__(msg, *args, **kwargs)


class EmptyWorkspaceException(WorkspaceError):
    """Workspace file is empty."""

    def __init__(
        self,
        *args: object,
        **kwargs: object,
    ) -> None:
        return super().__init__("Session configuration is empty.", *args, **kwargs)


class SessionMissingWorkspaceException(WorkspaceError, ObjectDoesNotExist):
    """Session missing while loading tmuxp workspace."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        return super().__init__(
            "No session object exists for WorkspaceBuilder. "
            "Tip: Add session_name in constructor or run WorkspaceBuilder.build()",
            *args,
            **kwargs,
        )


class ActiveSessionMissingWorkspaceException(WorkspaceError):
    """Active session cannot be found while loading tmuxp workspace."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        return super().__init__("No session active.", *args, **kwargs)


class TmuxpPluginException(TmuxpException):
    """Base Exception for Tmuxp Errors."""


class BeforeLoadScriptNotExists(OSError):
    """Raises if shell script could not be found."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)

        self.strerror = f"before_script file '{self.strerror}' doesn't exist."


@implements_to_string
class BeforeLoadScriptError(Exception):
    """Shell script execution error.

    Replaces :py:class:`subprocess.CalledProcessError` for
    :meth:`tmuxp.util.run_before_script`.
    """

    def __init__(
        self,
        returncode: int,
        cmd: str,
        output: t.Optional[str] = None,
    ) -> None:
        self.returncode = returncode
        self.cmd = cmd
        self.output = output
        self.message = (
            f"before_script failed with returncode {self.returncode}.\n"
            f"command: {self.cmd}\n"
            "Error output:\n"
            f"{self.output}"
        )

    def __str__(self) -> str:
        """Return shell error message."""
        return self.message
