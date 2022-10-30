from .. import exc


def validate_schema(workspace_dict):
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
        raise exc.WorkspaceError('workspace requires "session_name"')

    if "windows" not in workspace_dict:
        raise exc.WorkspaceError('workspace requires list of "windows"')

    for window in workspace_dict["windows"]:
        if "window_name" not in window:
            raise exc.WorkspaceError('workspace window is missing "window_name"')

    if "plugins" in workspace_dict:
        if not isinstance(workspace_dict["plugins"], list):
            raise exc.WorkspaceError('"plugins" only supports list type')

    return True
