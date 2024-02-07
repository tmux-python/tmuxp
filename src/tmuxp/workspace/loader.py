"""Workspace hydration and loading for tmuxp."""
import logging
import os
import pathlib
import typing as t

logger = logging.getLogger(__name__)


def expandshell(value: str) -> str:
    """Resolve shell variables based on user's ``$HOME`` and ``env``.

    :py:func:`os.path.expanduser` and :py:func:`os.path.expandvars`.

    Parameters
    ----------
    value : str
        value to expand

    Returns
    -------
    str
        value with shell variables expanded
    """
    return os.path.expandvars(os.path.expanduser(value))  # NOQA: PTH111


def expand_cmd(p: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
    """Resolve shell variables and expand shorthands in a tmuxp config mapping."""
    if isinstance(p, str):
        p = {"shell_command": [p]}
    elif isinstance(p, list):
        p = {"shell_command": p}
    elif not p:
        p = {"shell_command": []}

    assert isinstance(p, dict)
    if "shell_command" in p:
        cmds = p["shell_command"]

        if isinstance(p["shell_command"], str):
            cmds = [cmds]

        if not cmds or any(a == cmds for a in [None, "blank", "pane"]):
            cmds = []

        if (
            isinstance(cmds, list)
            and len(cmds) == 1
            and any(a in cmds for a in [None, "blank", "pane"])
        ):
            cmds = []

        for cmd_idx, cmd in enumerate(cmds):
            if isinstance(cmd, str):
                cmds[cmd_idx] = {"cmd": cmd}
            cmds[cmd_idx]["cmd"] = expandshell(cmds[cmd_idx]["cmd"])

        p["shell_command"] = cmds
    else:
        p["shell_command"] = []
    return p


def expand(
    workspace_dict: t.Dict[str, t.Any],
    cwd: t.Optional[t.Union[pathlib.Path, str]] = None,
    parent: t.Optional[t.Any] = None,
) -> t.Dict[str, t.Any]:
    """Resolve workspace variables and expand shorthand style / inline properties.

    This is necessary to keep the code in the :class:`WorkspaceBuilder` clean
    and also allow for neat, short-hand "sugarified" syntax.

    As a simple example, internally, tmuxp expects that workspace options
    like ``shell_command`` are a list (array)::

        'shell_command': ['htop']

    tmuxp workspace allow for it to be simply a string::

        'shell_command': 'htop'

    ConfigReader will load JSON/YAML files into python dicts for you.

    Parameters
    ----------
    workspace_dict : dict
        the tmuxp workspace for the session
    cwd : str
        directory to expand relative paths against. should be the dir of the
        workspace directory.
    parent : str
        (used on recursive entries) start_directory of parent window or session
        object.

    Returns
    -------
    dict
    """
    # Note: cli.py will expand workspaces relative to project's workspace directory
    # for the first cwd argument.
    cwd = pathlib.Path().cwd() if not cwd else pathlib.Path(cwd)

    if "session_name" in workspace_dict:
        workspace_dict["session_name"] = expandshell(workspace_dict["session_name"])
    if "window_name" in workspace_dict:
        workspace_dict["window_name"] = expandshell(workspace_dict["window_name"])
    if "environment" in workspace_dict:
        for key in workspace_dict["environment"]:
            val = workspace_dict["environment"][key]
            val = expandshell(val)
            if any(val.startswith(a) for a in [".", "./"]):
                val = str(cwd / val)
            workspace_dict["environment"][key] = val
    if "global_options" in workspace_dict:
        for key in workspace_dict["global_options"]:
            val = workspace_dict["global_options"][key]
            if isinstance(val, str):
                val = expandshell(val)
                if any(val.startswith(a) for a in [".", "./"]):
                    val = str(cwd / val)
            workspace_dict["global_options"][key] = val
    if "options" in workspace_dict:
        for key in workspace_dict["options"]:
            val = workspace_dict["options"][key]
            if isinstance(val, str):
                val = expandshell(val)
                if any(val.startswith(a) for a in [".", "./"]):
                    val = str(cwd / val)
            workspace_dict["options"][key] = val

    # Any workspace section, session, window, pane that can contain the
    # 'shell_command' value
    if "start_directory" in workspace_dict:
        workspace_dict["start_directory"] = expandshell(
            workspace_dict["start_directory"],
        )
        start_path = workspace_dict["start_directory"]
        if any(start_path.startswith(a) for a in [".", "./"]):
            # if window has a session, or pane has a window with a
            # start_directory of . or ./, make sure the start_directory can be
            # relative to the parent.
            #
            # This is for the case where you may be loading a workspace from
            # outside your shell current directory.
            if parent:
                cwd = pathlib.Path(parent["start_directory"])

            start_path = str((cwd / start_path).resolve(strict=False))

            workspace_dict["start_directory"] = start_path

    if "before_script" in workspace_dict:
        workspace_dict["before_script"] = expandshell(workspace_dict["before_script"])
        if any(workspace_dict["before_script"].startswith(a) for a in [".", "./"]):
            workspace_dict["before_script"] = str(cwd / workspace_dict["before_script"])

    if "shell_command" in workspace_dict and isinstance(
        workspace_dict["shell_command"],
        str,
    ):
        workspace_dict["shell_command"] = [workspace_dict["shell_command"]]

    if "shell_command_before" in workspace_dict:
        shell_command_before = workspace_dict["shell_command_before"]

        workspace_dict["shell_command_before"] = expand_cmd(shell_command_before)

    # recurse into window and pane workspace items
    if "windows" in workspace_dict:
        workspace_dict["windows"] = [
            expand(window, parent=workspace_dict)
            for window in workspace_dict["windows"]
        ]
    elif "panes" in workspace_dict:
        pane_dicts = workspace_dict["panes"]
        for pane_idx, pane_dict in enumerate(pane_dicts):
            pane_dicts[pane_idx] = {}
            pane_dicts[pane_idx].update(expand_cmd(pane_dict))
        workspace_dict["panes"] = [
            expand(pane, parent=workspace_dict) for pane in pane_dicts
        ]

    return workspace_dict


def trickle(workspace_dict: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
    """Return a dict with "trickled down" / inherited workspace values.

    This will only work if workspace has been expanded to full form with
    :meth:`loader.expand`.

    tmuxp allows certain commands to be default at the session, window
    level. shell_command_before trickles down and prepends the
    ``shell_command`` for the pane.

    Parameters
    ----------
    workspace_dict : dict
        the tmuxp workspace.

    Returns
    -------
    dict
    """
    # prepends a pane's ``shell_command`` list with the window and sessions'
    # ``shell_command_before``.

    session_start_directory = workspace_dict.get("start_directory")

    suppress_history = workspace_dict.get("suppress_history")

    for window_dict in workspace_dict["windows"]:
        # Prepend start_directory to relative window commands
        if session_start_directory:
            session_start_directory = session_start_directory
            if "start_directory" not in window_dict:
                window_dict["start_directory"] = session_start_directory
            else:
                if not any(
                    window_dict["start_directory"].startswith(a) for a in ["~", "/"]
                ):
                    window_start_path = (
                        pathlib.Path(session_start_directory)
                        / window_dict["start_directory"]
                    )
                    window_dict["start_directory"] = str(window_start_path)

        # We only need to trickle to the window, workspace builder checks wconf
        if suppress_history is not None and "suppress_history" not in window_dict:
            window_dict["suppress_history"] = suppress_history

        # If panes were NOT specified for a window, assume that a single pane
        # with no shell commands is desired
        if "panes" not in window_dict:
            window_dict["panes"] = [{"shell_command": []}]

        for pane_idx, pane_dict in enumerate(window_dict["panes"]):
            commands_before = []

            # Prepend shell_command_before to commands
            if "shell_command_before" in workspace_dict:
                commands_before.extend(
                    workspace_dict["shell_command_before"]["shell_command"],
                )
            if "shell_command_before" in window_dict:
                commands_before.extend(
                    window_dict["shell_command_before"]["shell_command"],
                )
            if "shell_command_before" in pane_dict:
                commands_before.extend(
                    pane_dict["shell_command_before"]["shell_command"],
                )

            if "shell_command" in pane_dict:
                commands_before.extend(pane_dict["shell_command"])

            window_dict["panes"][pane_idx]["shell_command"] = commands_before
            # pane_dict['shell_command'] = commands_before

    return workspace_dict
