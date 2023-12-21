"""Validation errors for tmuxp configuration files."""
import typing as t

from .. import exc


class SchemaValidationError(exc.WorkspaceError):
    """Tmuxp configuration validation base error."""

    pass


class SessionNameMissingValidationError(SchemaValidationError):
    """Tmuxp configuration error for session name missing."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        return super().__init__(
            'workspace requires "session_name"',
            *args,
            **kwargs,
        )


class WindowListMissingValidationError(SchemaValidationError):
    """Tmuxp configuration error for window list missing."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        return super().__init__(
            'workspace requires list of "windows"',
            *args,
            **kwargs,
        )


class WindowNameMissingValidationError(SchemaValidationError):
    """Tmuxp configuration error for missing window_name."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        return super().__init__(
            'workspace window is missing "window_name"',
            *args,
            **kwargs,
        )


class InvalidPluginsValidationError(SchemaValidationError):
    """Tmuxp configuration error for invalid plugins."""

    def __init__(self, plugins: t.Any, *args: object, **kwargs: object) -> None:
        return super().__init__(
            '"plugins" only supports list type. '
            + f" Received {type(plugins)}, "
            + f"value: {plugins}",
            *args,
            **kwargs,
        )


def validate_schema(workspace_dict: t.Any) -> bool:
    """
    Return True if workspace schema is correct.

    Parameters
    ----------
    workspace_dict : dict
        tmuxp workspace data

    Returns
    -------
    bool
    """
    # verify session_name
    if "session_name" not in workspace_dict:
        raise SessionNameMissingValidationError()

    if "windows" not in workspace_dict:
        raise WindowListMissingValidationError()

    for window in workspace_dict["windows"]:
        if "window_name" not in window:
            raise WindowNameMissingValidationError()

    if "plugins" in workspace_dict and not isinstance(workspace_dict["plugins"], list):
        raise InvalidPluginsValidationError(plugins=workspace_dict.get("plugins"))

    return True
