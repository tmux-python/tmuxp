"""Configuration import adapters to load teamocil, tmuxinator, etc. in tmuxp."""

from __future__ import annotations

import shlex
import typing as t


def import_tmuxinator(workspace_dict: dict[str, t.Any]) -> dict[str, t.Any]:
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
    tmuxp_workspace: dict[str, t.Any] = {}

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

    raw_args = workspace_dict.get("cli_args") or workspace_dict.get("tmux_options")
    if raw_args:
        tokens = shlex.split(raw_args)
        flag_map = {"-f": "config", "-L": "socket_name", "-S": "socket_path"}
        it = iter(tokens)
        for token in it:
            if token in flag_map:
                value = next(it, None)
                if value is not None:
                    tmuxp_workspace[flag_map[token]] = value

    if "socket_name" in workspace_dict:
        tmuxp_workspace["socket_name"] = workspace_dict["socket_name"]

    tmuxp_workspace["windows"] = []

    if "tabs" in workspace_dict:
        workspace_dict["windows"] = workspace_dict.pop("tabs")

    pre_window_val = workspace_dict.get(
        "pre_window",
        workspace_dict.get("pre_tab"),
    )

    if "pre" in workspace_dict and pre_window_val is not None:
        tmuxp_workspace["before_script"] = workspace_dict["pre"]

        if isinstance(pre_window_val, str):
            tmuxp_workspace["shell_command_before"] = [pre_window_val]
        else:
            tmuxp_workspace["shell_command_before"] = pre_window_val
    elif "pre" in workspace_dict:
        tmuxp_workspace["before_script"] = workspace_dict["pre"]

    if "rbenv" in workspace_dict:
        if "shell_command_before" not in tmuxp_workspace:
            tmuxp_workspace["shell_command_before"] = []
        tmuxp_workspace["shell_command_before"].append(
            "rbenv shell {}".format(workspace_dict["rbenv"]),
        )

    if "rvm" in workspace_dict:
        if "shell_command_before" not in tmuxp_workspace:
            tmuxp_workspace["shell_command_before"] = []
        tmuxp_workspace["shell_command_before"].append(
            "rvm use {}".format(workspace_dict["rvm"]),
        )

    if "startup_window" in workspace_dict:
        tmuxp_workspace["start_window"] = workspace_dict["startup_window"]

    if "startup_pane" in workspace_dict:
        tmuxp_workspace["start_pane"] = workspace_dict["startup_pane"]

    for window_dict in workspace_dict["windows"]:
        for k, v in window_dict.items():
            window_dict = {"window_name": k}

            if isinstance(v, str) or v is None:
                window_dict["panes"] = [v]
                tmuxp_workspace["windows"].append(window_dict)
                continue
            if isinstance(v, list):
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

            if "synchronize" in v:
                sync = v["synchronize"]
                if sync is True or sync == "before":
                    window_dict.setdefault("options", {})["synchronize-panes"] = "on"
                elif sync == "after":
                    window_dict.setdefault("options_after", {})["synchronize-panes"] = (
                        "on"
                    )

            tmuxp_workspace["windows"].append(window_dict)
    return tmuxp_workspace


def import_teamocil(workspace_dict: dict[str, t.Any]) -> dict[str, t.Any]:
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
    tmuxp_workspace: dict[str, t.Any] = {}

    if "session" in workspace_dict:
        workspace_dict = workspace_dict["session"]

    tmuxp_workspace["session_name"] = workspace_dict.get("name", None)

    if "root" in workspace_dict:
        tmuxp_workspace["start_directory"] = workspace_dict.pop("root")

    tmuxp_workspace["windows"] = []

    for w in workspace_dict["windows"]:
        window_dict = {"window_name": w["name"]}

        if "clear" in w:
            window_dict["clear"] = w["clear"]

        if "filters" in w:
            if w["filters"].get("before"):
                window_dict["shell_command_before"] = w["filters"]["before"]
            if w["filters"].get("after"):
                window_dict["shell_command_after"] = w["filters"]["after"]

        if "root" in w:
            window_dict["start_directory"] = w.pop("root")

        if "splits" in w:
            w["panes"] = w.pop("splits")

        if "panes" in w:
            panes: list[t.Any] = []
            for p in w["panes"]:
                if p is None:
                    panes.append({"shell_command": []})
                elif isinstance(p, str):
                    panes.append({"shell_command": [p]})
                else:
                    if "cmd" in p:
                        p["shell_command"] = p.pop("cmd")
                    elif "commands" in p:
                        p["shell_command"] = p.pop("commands")
                    if "width" in p:
                        p.pop("width")
                    if "height" in p:
                        p.pop("height")
                    panes.append(p)
            window_dict["panes"] = panes

        if "layout" in w:
            window_dict["layout"] = w["layout"]

        if w.get("focus"):
            window_dict["focus"] = True

        if "options" in w:
            window_dict["options"] = w["options"]

        tmuxp_workspace["windows"].append(window_dict)

    return tmuxp_workspace
