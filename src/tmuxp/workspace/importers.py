"""Configuration import adapters to load teamocil, tmuxinator, etc. in tmuxp."""

from __future__ import annotations

import logging
import shlex
import typing as t

logger = logging.getLogger(__name__)


def _join_tmuxinator_parameters(parameters: t.Any) -> str | None:
    """Return tmuxinator's command-parameter string.

    Tmuxinator joins array-valued project parameters with a semicolon-space
    separator before sending them to tmux.

    Examples
    --------
    >>> _join_tmuxinator_parameters(["one", "two"])
    'one; two'
    >>> _join_tmuxinator_parameters("one")
    'one'
    >>> _join_tmuxinator_parameters(None) is None
    True
    """
    if parameters is None:
        return None
    if isinstance(parameters, list):
        return "; ".join(str(parameter) for parameter in parameters)
    return str(parameters)


def _parse_tmux_options(raw_args: str) -> dict[str, str]:
    """Parse tmux pass-through flags from tmuxinator args.

    Examples
    --------
    >>> _parse_tmux_options("-f ~/.tmux.conf -L mysocket")
    {'config': '~/.tmux.conf', 'socket_name': 'mysocket'}
    >>> _parse_tmux_options("-f./tmux.conf -S/tmp/tmux.sock")
    {'config': './tmux.conf', 'socket_path': '/tmp/tmux.sock'}
    """
    flag_map = {"-f": "config", "-L": "socket_name", "-S": "socket_path"}
    result: dict[str, str] = {}
    tokens = shlex.split(raw_args)
    token_index = 0

    while token_index < len(tokens):
        token = tokens[token_index]
        if token in flag_map:
            token_index += 1
            if token_index < len(tokens):
                result[flag_map[token]] = tokens[token_index]
        else:
            for prefix, key in flag_map.items():
                if token.startswith(prefix) and len(token) > len(prefix):
                    result[key] = token[len(prefix) :]
                    break
        token_index += 1

    return result


def _convert_named_panes(panes: list[t.Any]) -> list[t.Any]:
    """Convert tmuxinator named pane dictionaries to tmuxp pane titles.

    Examples
    --------
    >>> _convert_named_panes(["vim", {"logs": ["tail -f log"]}])
    ['vim', {'shell_command': ['tail -f log'], 'title': 'logs'}]
    >>> _convert_named_panes([{"empty": None}])
    [{'shell_command': [], 'title': 'empty'}]
    """
    result: list[t.Any] = []
    for pane in panes:
        if isinstance(pane, dict) and len(pane) == 1 and "shell_command" not in pane:
            pane_name = next(iter(pane))
            commands = pane[pane_name]
            if isinstance(commands, str):
                shell_command: list[t.Any] = [commands]
            elif commands is None:
                shell_command = []
            elif isinstance(commands, list):
                shell_command = commands
            else:
                shell_command = [commands]
            result.append(
                {
                    "shell_command": shell_command,
                    "title": str(pane_name),
                }
            )
        else:
            result.append(pane)
    return result


def _resolve_tmux_list_position(
    target: str | int,
    *,
    base_index: int,
    item_count: int,
) -> int | None:
    """Resolve a tmux index to a Python list position.

    Examples
    --------
    >>> _resolve_tmux_list_position(1, base_index=1, item_count=2)
    0
    >>> _resolve_tmux_list_position("2", base_index=1, item_count=2)
    1
    >>> _resolve_tmux_list_position(3, base_index=1, item_count=2) is None
    True
    """
    try:
        list_position = int(target) - base_index
    except ValueError:
        return None

    if 0 <= list_position < item_count:
        return list_position
    return None


def _focus_tmuxinator_startup_target(
    tmuxp_workspace: dict[str, t.Any],
    startup_window: str | int | None,
    startup_pane: str | int | None,
    *,
    base_index: int,
    pane_base_index: int,
) -> None:
    """Apply tmuxinator startup focus keys to a tmuxp workspace.

    Examples
    --------
    >>> workspace = {"windows": [{"window_name": "main", "panes": ["vim"]}]}
    >>> _focus_tmuxinator_startup_target(
    ...     workspace, "main", 0, base_index=0, pane_base_index=0
    ... )
    >>> workspace["windows"][0]["focus"]
    True
    >>> workspace["windows"][0]["panes"][0]
    {'shell_command': ['vim'], 'focus': True}
    """
    windows = tmuxp_workspace.get("windows", [])
    if not windows:
        return

    target_window = windows[0]
    if startup_window is not None:
        target_window = {}
        for window in windows:
            if window.get("window_name") == str(startup_window):
                target_window = window
                break
        if not target_window:
            window_index = _resolve_tmux_list_position(
                startup_window,
                base_index=base_index,
                item_count=len(windows),
            )
            if window_index is None:
                logger.warning(
                    "startup_window %r not found for tmux base-index %d",
                    startup_window,
                    base_index,
                )
                return
            target_window = windows[window_index]

        target_window["focus"] = True
    elif startup_pane is not None:
        target_window["focus"] = True

    if startup_pane is None or "panes" not in target_window:
        return

    panes = target_window["panes"]
    pane_index = _resolve_tmux_list_position(
        startup_pane,
        base_index=pane_base_index,
        item_count=len(panes),
    )
    if pane_index is None:
        logger.warning(
            "startup_pane %r not found for tmux pane-base-index %d",
            startup_pane,
            pane_base_index,
        )
        return

    pane = panes[pane_index]
    if isinstance(pane, dict):
        pane["focus"] = True
    else:
        panes[pane_index] = {
            "shell_command": [pane] if pane else [],
            "focus": True,
        }


def import_tmuxinator(
    workspace_dict: dict[str, t.Any],
    *,
    base_index: int = 0,
    pane_base_index: int = 0,
) -> dict[str, t.Any]:
    """Return tmuxp workspace from a ``tmuxinator`` yaml workspace.

    Parameters
    ----------
    workspace_dict : dict
        python dict for tmuxp workspace.
    base_index : int
        tmux ``base-index`` used to resolve numeric ``startup_window``.
    pane_base_index : int
        tmux ``pane-base-index`` used to resolve numeric ``startup_pane``.

    Returns
    -------
    dict

    Examples
    --------
    >>> result = import_tmuxinator(
    ...     {"name": "demo", "windows": [{"editor": {"panes": ["vim"]}}]}
    ... )
    >>> result["session_name"]
    'demo'
    >>> result["windows"][0]["window_name"]
    'editor'
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

    raw_tmux_options = workspace_dict.get("cli_args") or workspace_dict.get(
        "tmux_options",
    )
    if raw_tmux_options:
        tmuxp_workspace.update(_parse_tmux_options(str(raw_tmux_options)))

    for socket_key in ("socket_name", "socket_path"):
        if socket_key in workspace_dict:
            explicit_value = workspace_dict[socket_key]
            if (
                socket_key in tmuxp_workspace
                and tmuxp_workspace[socket_key] != explicit_value
            ):
                logger.warning(
                    "explicit %s %s overrides tmux option value %s",
                    socket_key,
                    explicit_value,
                    tmuxp_workspace[socket_key],
                )
            tmuxp_workspace[socket_key] = explicit_value

    for pass_key in (
        "enable_pane_titles",
        "pane_title_position",
        "pane_title_format",
        "on_project_start",
        "on_project_restart",
        "on_project_exit",
        "on_project_stop",
    ):
        if pass_key in workspace_dict:
            tmuxp_workspace[pass_key] = workspace_dict[pass_key]

    if "pre" in workspace_dict and "on_project_start" not in tmuxp_workspace:
        pre_command = _join_tmuxinator_parameters(workspace_dict["pre"])
        if pre_command is not None:
            tmuxp_workspace["on_project_start"] = pre_command

    pre_window = None
    if "rbenv" in workspace_dict:
        pre_window = "rbenv shell {}".format(workspace_dict["rbenv"])
    elif "rvm" in workspace_dict:
        pre_window = "rvm use {}".format(workspace_dict["rvm"])
    elif "pre_tab" in workspace_dict:
        pre_window = _join_tmuxinator_parameters(workspace_dict["pre_tab"])
    elif "pre_window" in workspace_dict:
        pre_window = _join_tmuxinator_parameters(workspace_dict["pre_window"])

    if pre_window is not None:
        tmuxp_workspace["shell_command_before"] = [pre_window]

    if "on_project_first_start" in workspace_dict:
        logger.warning(
            "on_project_first_start is not yet supported by tmuxp; "
            "consider using on_project_start instead",
        )

    for unsupported_key, hint in {
        "tmux_command": "custom tmux binary is not supported; tmuxp always uses tmux",
        "attach": "use tmuxp load -d for detached mode instead",
        "post": "deprecated in tmuxinator; use on_project_exit or on_project_stop",
    }.items():
        if unsupported_key in workspace_dict:
            logger.warning(
                "tmuxinator key %r is not supported by tmuxp: %s",
                unsupported_key,
                hint,
            )

    tmuxp_workspace["windows"] = []

    if "tabs" in workspace_dict:
        workspace_dict["windows"] = workspace_dict.pop("tabs")

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
            if "synchronize" in v and v["synchronize"] in (True, "before", "after"):
                window_dict["synchronize"] = v["synchronize"]
            tmuxp_workspace["windows"].append(window_dict)

    _focus_tmuxinator_startup_target(
        tmuxp_workspace,
        workspace_dict.get("startup_window"),
        workspace_dict.get("startup_pane"),
        base_index=base_index,
        pane_base_index=pane_base_index,
    )
    return tmuxp_workspace


def import_teamocil(workspace_dict: dict[str, t.Any]) -> dict[str, t.Any]:
    """Return tmuxp workspace from a ``teamocil`` yaml workspace.

    Parameters
    ----------
    workspace_dict : dict
        python dict for tmuxp workspace

    Examples
    --------
    >>> result = import_teamocil(
    ...     {"windows": [{"name": "dev", "panes": [{"cmd": "ls"}]}]}
    ... )
    >>> result["windows"][0]["panes"]
    [{'shell_command': 'ls'}]

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
                    continue
                if isinstance(p, str):
                    panes.append({"shell_command": [p]})
                    continue
                if not isinstance(p, dict):
                    panes.append({"shell_command": [str(p)]})
                    continue
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
        tmuxp_workspace["windows"].append(window_dict)

    return tmuxp_workspace
