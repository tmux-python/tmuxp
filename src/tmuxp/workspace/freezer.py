def inline(workspace_dict):
    """Return workspace with inlined shorthands. Opposite of :meth:`loader.expand`.

    Parameters
    ----------
    workspace_dict : dict

    Returns
    -------
    dict
        workspace with shorthands inlined.
    """

    if (
        "shell_command" in workspace_dict
        and isinstance(workspace_dict["shell_command"], list)
        and len(workspace_dict["shell_command"]) == 1
    ):
        workspace_dict["shell_command"] = workspace_dict["shell_command"][0]

        if len(workspace_dict.keys()) == int(1):
            workspace_dict = workspace_dict["shell_command"]
    if (
        "shell_command_before" in workspace_dict
        and isinstance(workspace_dict["shell_command_before"], list)
        and len(workspace_dict["shell_command_before"]) == 1
    ):
        workspace_dict["shell_command_before"] = workspace_dict["shell_command_before"][
            0
        ]

    # recurse into window and pane workspace items
    if "windows" in workspace_dict:
        workspace_dict["windows"] = [
            inline(window) for window in workspace_dict["windows"]
        ]
    if "panes" in workspace_dict:
        workspace_dict["panes"] = [inline(pane) for pane in workspace_dict["panes"]]

    return workspace_dict


def freeze(session):
    """Freeze live tmux session into a tmuxp workspacee.

    Parameters
    ----------
    session : :class:`libtmux.Session`
        session object

    Returns
    -------
    dict
        tmuxp compatible workspace
    """
    sconf = {"session_name": session["session_name"], "windows": []}

    for w in session.windows:
        wconf = {
            "options": w.show_window_options(),
            "window_name": w.name,
            "layout": w.layout,
            "panes": [],
        }
        if w.get("window_active", "0") == "1":
            wconf["focus"] = "true"

        # If all panes have same path, set 'start_directory' instead
        # of using 'cd' shell commands.
        def pane_has_same_path(p):
            return w.panes[0].current_path == p.current_path

        if all(pane_has_same_path(p) for p in w.panes):
            wconf["start_directory"] = w.panes[0].current_path

        for p in w.panes:
            pconf = {"shell_command": []}

            if "start_directory" not in wconf:
                pconf["shell_command"].append("cd " + p.current_path)

            if p.get("pane_active", "0") == "1":
                pconf["focus"] = "true"

            current_cmd = p.current_command

            def filter_interpretters_and_shells():
                return current_cmd.startswith("-") or any(
                    current_cmd.endswith(cmd) for cmd in ["python", "ruby", "node"]
                )

            if filter_interpretters_and_shells():
                current_cmd = None

            if current_cmd:
                pconf["shell_command"].append(current_cmd)
            else:
                if not len(pconf["shell_command"]):
                    pconf = "pane"

            wconf["panes"].append(pconf)

        sconf["windows"].append(wconf)

    return sconf
