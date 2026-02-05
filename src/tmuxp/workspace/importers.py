"""Configuration import adapters to load teamocil, tmuxinator, etc. in tmuxp."""

from __future__ import annotations

import logging
import typing as t

logger = logging.getLogger(__name__)


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

    # Handle pre/pre_window/pre_tab combinations
    # pre_tab is deprecated alias for pre_window
    pre_window = workspace_dict.get("pre_window") or workspace_dict.get("pre_tab")

    if "pre" in workspace_dict and pre_window:
        # Both present: pre -> session shell_command, pre_window -> shell_command_before
        tmuxp_workspace["shell_command"] = workspace_dict["pre"]
        if isinstance(pre_window, str):
            tmuxp_workspace["shell_command_before"] = [pre_window]
        else:
            tmuxp_workspace["shell_command_before"] = pre_window
    elif pre_window:
        # Only pre_window: use it as shell_command_before
        if isinstance(pre_window, str):
            tmuxp_workspace["shell_command_before"] = [pre_window]
        else:
            tmuxp_workspace["shell_command_before"] = pre_window
    elif "pre" in workspace_dict:
        # Only pre: use it as shell_command_before
        pre = workspace_dict["pre"]
        if isinstance(pre, str):
            tmuxp_workspace["shell_command_before"] = [pre]
        else:
            tmuxp_workspace["shell_command_before"] = pre

    # Handle rbenv and rvm version managers
    if "rbenv" in workspace_dict:
        if "shell_command_before" not in tmuxp_workspace:
            tmuxp_workspace["shell_command_before"] = []
        tmuxp_workspace["shell_command_before"].append(
            f"rbenv shell {workspace_dict['rbenv']}",
        )

    if "rvm" in workspace_dict:
        if "shell_command_before" not in tmuxp_workspace:
            tmuxp_workspace["shell_command_before"] = []
        tmuxp_workspace["shell_command_before"].append(
            f"rvm use {workspace_dict['rvm']}",
        )

    # Warn about unsupported 'post' key
    if "post" in workspace_dict:
        logger.warning(
            "tmuxinator 'post' key is not supported by tmuxp and will be ignored"
        )

    for orig_window in workspace_dict["windows"]:
        for k, v in orig_window.items():
            new_window: dict[str, t.Any] = {"window_name": k}

            if isinstance(v, str) or v is None:
                new_window["panes"] = [v]
                tmuxp_workspace["windows"].append(new_window)
                continue
            if isinstance(v, list):
                new_window["panes"] = v
                tmuxp_workspace["windows"].append(new_window)
                continue

            if "pre" in v:
                new_window["shell_command_before"] = v["pre"]
            if "panes" in v:
                new_window["panes"] = v["panes"]
            if "root" in v:
                new_window["start_directory"] = v["root"]

            if "layout" in v:
                new_window["layout"] = v["layout"]

            # Handle synchronize option -> options_after
            if "synchronize" in v:
                sync_val = v["synchronize"]
                if sync_val in (True, "before"):
                    new_window["options"] = {"synchronize-panes": "on"}
                elif sync_val == "after":
                    new_window["options_after"] = {"synchronize-panes": "on"}

            tmuxp_workspace["windows"].append(new_window)

    # Handle startup_window - set focus: true on matching window
    if "startup_window" in workspace_dict:
        startup_window = workspace_dict["startup_window"]
        for w in tmuxp_workspace["windows"]:
            if w.get("window_name") == startup_window:
                w["focus"] = True
                break

    # Handle startup_pane - set focus: true on matching pane in focused window
    if "startup_pane" in workspace_dict:
        startup_pane = workspace_dict["startup_pane"]
        # Find the focused window (or first window if none focused)
        target_window = None
        for w in tmuxp_workspace["windows"]:
            if w.get("focus"):
                target_window = w
                break
        if target_window is None and tmuxp_workspace["windows"]:
            target_window = tmuxp_workspace["windows"][0]

        if target_window and "panes" in target_window:
            panes = target_window["panes"]
            if isinstance(startup_pane, int) and 0 <= startup_pane < len(panes):
                # Convert simple pane to dict if needed
                pane = panes[startup_pane]
                if isinstance(pane, str) or pane is None:
                    panes[startup_pane] = {"shell_command": [pane] if pane else []}
                    pane = panes[startup_pane]
                elif isinstance(pane, list):
                    panes[startup_pane] = {"shell_command": pane}
                    pane = panes[startup_pane]
                if isinstance(pane, dict):
                    pane["focus"] = True

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
            if "before" in w["filters"]:
                for _b in w["filters"]["before"]:
                    window_dict["shell_command_before"] = w["filters"]["before"]
            if "after" in w["filters"]:
                for _b in w["filters"]["after"]:
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
                    # TODO support for height/width
                    p.pop("width")
            window_dict["panes"] = w["panes"]

        if "layout" in w:
            window_dict["layout"] = w["layout"]
        tmuxp_workspace["windows"].append(window_dict)

    return tmuxp_workspace
