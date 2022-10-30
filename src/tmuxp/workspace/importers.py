def import_tmuxinator(workspace_dict):
    """Return tmuxp workspace from a `tmuxinator`_ yaml workspace.

    .. _tmuxinator: https://github.com/aziz/tmuxinator

    Parameters
    ----------
    workspace_dict : dict
        python dict for tmuxp workspace.

    Returns
    -------
    dict
    """

    tmuxp_workspace = {}

    if "project_name" in workspace_dict:
        tmuxp_workspace["session_name"] = workspace_dict.pop("project_name")
    elif "name" in workspace_dict:
        tmuxp_workspace["session_name"] = workspace_dict.pop("name")
    else:
        tmuxp_workspace["session_name"] = None

    if "project_root" in workspace_dict:
        tmuxp_workspace["start_directory"] = workspace_dict.pop("project_root")
    elif "root" in workspace_dict:
        tmuxp_workspace["start_directory"] = workspace_dict.pop("root")

    if "cli_args" in workspace_dict:
        tmuxp_workspace["config"] = workspace_dict["cli_args"]

        if "-f" in tmuxp_workspace["config"]:
            tmuxp_workspace["config"] = (
                tmuxp_workspace["config"].replace("-f", "").strip()
            )
    elif "tmux_options" in workspace_dict:
        tmuxp_workspace["config"] = workspace_dict["tmux_options"]

        if "-f" in tmuxp_workspace["config"]:
            tmuxp_workspace["config"] = (
                tmuxp_workspace["config"].replace("-f", "").strip()
            )

    if "socket_name" in workspace_dict:
        tmuxp_workspace["socket_name"] = workspace_dict["socket_name"]

    tmuxp_workspace["windows"] = []

    if "tabs" in workspace_dict:
        workspace_dict["windows"] = workspace_dict.pop("tabs")

    if "pre" in workspace_dict and "pre_window" in workspace_dict:
        tmuxp_workspace["shell_command"] = workspace_dict["pre"]

        if isinstance(workspace_dict["pre"], str):
            tmuxp_workspace["shell_command_before"] = [workspace_dict["pre_window"]]
        else:
            tmuxp_workspace["shell_command_before"] = workspace_dict["pre_window"]
    elif "pre" in workspace_dict:
        if isinstance(workspace_dict["pre"], str):
            tmuxp_workspace["shell_command_before"] = [workspace_dict["pre"]]
        else:
            tmuxp_workspace["shell_command_before"] = workspace_dict["pre"]

    if "rbenv" in workspace_dict:
        if "shell_command_before" not in tmuxp_workspace:
            tmuxp_workspace["shell_command_before"] = []
        tmuxp_workspace["shell_command_before"].append(
            "rbenv shell %s" % workspace_dict["rbenv"]
        )

    for window_dict in workspace_dict["windows"]:
        for k, v in window_dict.items():
            window_dict = {"window_name": k}

            if isinstance(v, str) or v is None:
                window_dict["panes"] = [v]
                tmuxp_workspace["windows"].append(window_dict)
                continue
            elif isinstance(v, list):
                window_dict["panes"] = v
                tmuxp_workspace["windows"].append(window_dict)
                continue

            if "pre" in v:
                window_dict["shell_command_before"] = v["pre"]
            if "panes" in v:
                window_dict["panes"] = v["panes"]
            if "root" in v:
                window_dict["start_directory"] = v["root"]

            if "layout" in v:
                window_dict["layout"] = v["layout"]
            tmuxp_workspace["windows"].append(window_dict)
    return tmuxp_workspace


def import_teamocil(workspace_dict):
    """Return tmuxp workspace from a `teamocil`_ yaml workspace.

    .. _teamocil: https://github.com/remiprev/teamocil

    Parameters
    ----------
    workspace_dict : dict
        python dict for tmuxp workspace

    Notes
    -----

    Todos:

    - change  'root' to a cd or start_directory
    - width in pane -> main-pain-width
    - with_env_var
    - clear
    - cmd_separator
    """

    tmuxp_workspace = {}

    if "session" in workspace_dict:
        workspace_dict = workspace_dict["session"]

    if "name" in workspace_dict:
        tmuxp_workspace["session_name"] = workspace_dict["name"]
    else:
        tmuxp_workspace["session_name"] = None

    if "root" in workspace_dict:
        tmuxp_workspace["start_directory"] = workspace_dict.pop("root")

    tmuxp_workspace["windows"] = []

    for w in workspace_dict["windows"]:
        window_dict = {"window_name": w["name"]}

        if "clear" in w:
            window_dict["clear"] = w["clear"]

        if "filters" in w:
            if "before" in w["filters"]:
                for b in w["filters"]["before"]:
                    window_dict["shell_command_before"] = w["filters"]["before"]
            if "after" in w["filters"]:
                for b in w["filters"]["after"]:
                    window_dict["shell_command_after"] = w["filters"]["after"]

        if "root" in w:
            window_dict["start_directory"] = w.pop("root")

        if "splits" in w:
            w["panes"] = w.pop("splits")

        if "panes" in w:
            for p in w["panes"]:
                if "cmd" in p:
                    p["shell_command"] = p.pop("cmd")
                if "width" in p:
                    # todo support for height/width
                    p.pop("width")
            window_dict["panes"] = w["panes"]

        if "layout" in w:
            window_dict["layout"] = w["layout"]
        tmuxp_workspace["windows"].append(window_dict)

    return tmuxp_workspace
