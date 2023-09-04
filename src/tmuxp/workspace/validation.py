import typing as t

from .. import exc


class SchemaValidationError(exc.WorkspaceError):
    pass


class SessionNameMissingValidationError(SchemaValidationError):
    def __init__(self, *args: object, **kwargs: object) -> None:
        return super().__init__(
            'workspace requires "session_name"',
            *args,
            **kwargs,
        )


class WindowListMissingValidationError(SchemaValidationError):
    def __init__(self, *args: object, **kwargs: object) -> None:
        return super().__init__(
            'workspace requires list of "windows"',
            *args,
            **kwargs,
        )


class WindowNameMissingValidationError(SchemaValidationError):
    def __init__(self, *args: object, **kwargs: object) -> None:
        return super().__init__(
            'workspace window is missing "window_name"',
            *args,
            **kwargs,
        )


class InvalidPluginsValidationError(SchemaValidationError):
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
