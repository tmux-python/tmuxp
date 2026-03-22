"""Configuration import adapters to load teamocil, tmuxinator, etc. in tmuxp."""

from __future__ import annotations

import logging
import shlex
import typing as t

logger = logging.getLogger(__name__)


def _convert_named_panes(panes: list[t.Any]) -> list[t.Any]:
    """Convert tmuxinator named pane dicts to tmuxp format.

    Tmuxinator supports ``{pane_name: commands}`` dicts in pane lists, where the
    key is the pane title and the value is the command or command list.  Convert
    these to ``{"shell_command": commands, "title": pane_name}`` so the builder
    can call ``pane.set_title()``.

    Parameters
    ----------
    panes : list
        Raw pane list from a tmuxinator window config.

    Returns
    -------
    list
        Pane list with named pane dicts converted.

    Examples
    --------
    >>> _convert_named_panes(["vim", {"logs": ["tail -f log"]}])
    ['vim', {'shell_command': ['tail -f log'], 'title': 'logs'}]

    >>> _convert_named_panes(["vim", None, "top"])
    ['vim', None, 'top']
    """
    result: list[t.Any] = []
    for pane in panes:
        if isinstance(pane, dict) and len(pane) == 1 and "shell_command" not in pane:
            pane_name = next(iter(pane))
            commands = pane[pane_name]
            if isinstance(commands, str):
                commands = [commands]
            elif commands is None:
                commands = []
            result.append(
                {
                    "shell_command": commands,
                    "title": str(pane_name),
                }
            )
        else:
            result.append(pane)
    return result


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
    logger.debug(
        "importing tmuxinator workspace",
        extra={
            "tmux_session": workspace_dict.get("project_name")
            or workspace_dict.get("name", ""),
        },
    )

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
        explicit_name = workspace_dict["socket_name"]
        if (
            "socket_name" in tmuxp_workspace
            and tmuxp_workspace["socket_name"] != explicit_name
        ):
            logger.warning(
                "explicit socket_name %s overrides -L %s from cli_args",
                explicit_name,
                tmuxp_workspace["socket_name"],
            )
        tmuxp_workspace["socket_name"] = explicit_name

    # Passthrough keys supported by both tmuxinator and tmuxp
    for _pass_key in (
        "enable_pane_titles",
        "pane_title_position",
        "pane_title_format",
        "on_project_start",
        "on_project_restart",
        "on_project_exit",
        "on_project_stop",
    ):
        if _pass_key in workspace_dict:
            tmuxp_workspace[_pass_key] = workspace_dict[_pass_key]

    if "on_project_first_start" in workspace_dict:
        logger.warning(
            "on_project_first_start is not yet supported by tmuxp; "
            "consider using on_project_start instead",
        )

    # Warn on tmuxinator keys that have no tmuxp equivalent
    _TMUXINATOR_UNMAPPED_KEYS = {
        "tmux_command": "custom tmux binary is not supported; tmuxp always uses 'tmux'",
        "attach": "use 'tmuxp load -d' for detached mode instead",
        "post": "deprecated in tmuxinator; use on_project_exit instead",
    }
    for _ukey, _uhint in _TMUXINATOR_UNMAPPED_KEYS.items():
        if _ukey in workspace_dict:
            logger.warning(
                "tmuxinator key %r is not supported by tmuxp: %s",
                _ukey,
                _uhint,
            )

    tmuxp_workspace["windows"] = []

    if "tabs" in workspace_dict:
        workspace_dict["windows"] = workspace_dict.pop("tabs")

    pre_window_val = workspace_dict.get(
        "pre_window",
        workspace_dict.get("pre_tab"),
    )

    if "pre" in workspace_dict and pre_window_val is not None:
        pre_val = workspace_dict["pre"]
        if isinstance(pre_val, list):
            tmuxp_workspace["before_script"] = "; ".join(pre_val)
        else:
            tmuxp_workspace["before_script"] = pre_val

        if isinstance(pre_window_val, str):
            tmuxp_workspace["shell_command_before"] = [pre_window_val]
        else:
            tmuxp_workspace["shell_command_before"] = pre_window_val
    elif "pre" in workspace_dict:
        pre_val = workspace_dict["pre"]
        if isinstance(pre_val, list):
            logger.info(
                "multi-command pre list mapped to before_script; "
                "consider splitting into before_script and shell_command_before",
            )
            tmuxp_workspace["before_script"] = "; ".join(pre_val)
        else:
            tmuxp_workspace["before_script"] = pre_val
    elif pre_window_val is not None:
        # pre_window/pre_tab without pre — tmuxinator treats these independently
        if isinstance(pre_window_val, list):
            tmuxp_workspace["shell_command_before"] = ["; ".join(pre_window_val)]
        elif isinstance(pre_window_val, str):
            tmuxp_workspace["shell_command_before"] = [pre_window_val]
        else:
            tmuxp_workspace["shell_command_before"] = pre_window_val

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

    _startup_window = workspace_dict.get("startup_window")
    _startup_pane = workspace_dict.get("startup_pane")

    for window_dict in workspace_dict["windows"]:
        for k, v in window_dict.items():
            window_dict = {"window_name": str(k) if k is not None else k}

            if isinstance(v, str) or v is None:
                window_dict["panes"] = [v]
                tmuxp_workspace["windows"].append(window_dict)
                continue
            if isinstance(v, list):
                window_dict["panes"] = _convert_named_panes(v)
                tmuxp_workspace["windows"].append(window_dict)
                continue

            if "pre" in v:
                window_dict["shell_command_before"] = v["pre"]
            if "panes" in v:
                window_dict["panes"] = _convert_named_panes(v["panes"])
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

    # Post-process startup_window / startup_pane into focus flags
    if _startup_window is not None and tmuxp_workspace["windows"]:
        _matched = False
        for w in tmuxp_workspace["windows"]:
            if w.get("window_name") == str(_startup_window):
                w["focus"] = True
                _matched = True
                break
        if not _matched:
            try:
                _idx = int(_startup_window)
                if 0 <= _idx < len(tmuxp_workspace["windows"]):
                    tmuxp_workspace["windows"][_idx]["focus"] = True
                    logger.info(
                        "startup_window %r resolved as 0-based list index; "
                        "use window name for unambiguous matching across tools",
                        _startup_window,
                    )
                else:
                    logger.warning(
                        "startup_window index %d out of range (0-%d)",
                        _idx,
                        len(tmuxp_workspace["windows"]) - 1,
                    )
            except (ValueError, IndexError):
                logger.warning(
                    "startup_window %s not found",
                    _startup_window,
                )

    if _startup_pane is not None and tmuxp_workspace["windows"]:
        _target = next(
            (w for w in tmuxp_workspace["windows"] if w.get("focus")),
            tmuxp_workspace["windows"][0],
        )
        if "panes" in _target:
            try:
                _pidx = int(_startup_pane)
                if 0 <= _pidx < len(_target["panes"]):
                    _pane = _target["panes"][_pidx]
                    if isinstance(_pane, dict):
                        _pane["focus"] = True
                    else:
                        _target["panes"][_pidx] = {
                            "shell_command": [_pane] if _pane else [],
                            "focus": True,
                        }
                    logger.info(
                        "startup_pane %r resolved as 0-based list index; "
                        "use window name + pane index for clarity",
                        _startup_pane,
                    )
                else:
                    logger.warning(
                        "startup_pane index %d out of range (0-%d)",
                        _pidx,
                        len(_target["panes"]) - 1,
                    )
            except (ValueError, IndexError):
                logger.warning(
                    "startup_pane %s not found",
                    _startup_pane,
                )

    return tmuxp_workspace


def import_teamocil(workspace_dict: dict[str, t.Any]) -> dict[str, t.Any]:
    """Return tmuxp workspace from a `teamocil`_ yaml workspace.

    .. _teamocil: https://github.com/remiprev/teamocil

    Parameters
    ----------
    workspace_dict : dict
        python dict for tmuxp workspace
    """
    _inner = workspace_dict.get("session", workspace_dict)
    logger.debug(
        "importing teamocil workspace",
        extra={"tmux_session": _inner.get("name", "")},
    )

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
                        logger.warning(
                            "unsupported pane key %s dropped",
                            "width",
                            extra={"tmux_window": w["name"]},
                        )
                        p.pop("width")
                    if "height" in p:
                        logger.warning(
                            "unsupported pane key %s dropped",
                            "height",
                            extra={"tmux_window": w["name"]},
                        )
                        p.pop("height")
                    panes.append(p)
            window_dict["panes"] = panes

        if "layout" in w:
            window_dict["layout"] = w["layout"]

        if w.get("focus"):
            window_dict["focus"] = True

        if "options" in w:
            window_dict["options"] = w["options"]

        if "with_env_var" in w:
            logger.warning(
                "unsupported window key %s dropped",
                "with_env_var",
                extra={"tmux_window": w["name"]},
            )

        if "cmd_separator" in w:
            logger.warning(
                "unsupported window key %s dropped",
                "cmd_separator",
                extra={"tmux_window": w["name"]},
            )

        tmuxp_workspace["windows"].append(window_dict)

    return tmuxp_workspace
