"""Configuration import adapters to load teamocil, tmuxinator, etc. in tmuxp."""

from __future__ import annotations

import logging
import shlex
import typing as t

logger = logging.getLogger(__name__)

_TMUXINATOR_UNMAPPED_KEYS: dict[str, str] = {
    "tmux_command": "custom tmux binary is not supported; tmuxp always uses 'tmux'",
    "attach": "use 'tmuxp load -d' for detached mode instead",
    "post": "deprecated in tmuxinator; use on_project_exit instead",
}


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


def _resolve_tmux_list_position(
    target: str | int,
    *,
    base_index: int,
    item_count: int,
) -> int | None:
    """Resolve a tmux index into a Python list position.

    Parameters
    ----------
    target : str or int
        tmux index from tmuxinator configuration
    base_index : int
        tmux base index for the list being resolved
    item_count : int
        number of items in the generated tmuxp list

    Returns
    -------
    int or None
        Python list position if the target resolves within bounds

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


def import_tmuxinator(
    workspace_dict: dict[str, t.Any],
    *,
    base_index: int = 0,
    pane_base_index: int = 0,
) -> dict[str, t.Any]:
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
                # Space-separated: -L mysocket
                value = next(it, None)
                if value is not None:
                    tmuxp_workspace[flag_map[token]] = value
            else:
                # Attached form: -Lmysocket
                for prefix, key in flag_map.items():
                    if token.startswith(prefix) and len(token) > len(prefix):
                        tmuxp_workspace[key] = token[len(prefix) :]
                        break

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

    # Handle pre → on_project_start (independent of pre_window chain)
    # tmuxinator's pre is a raw shell command emitted as a line in a bash script.
    # on_project_start uses run_hook_commands(shell=True) which handles raw commands.
    # before_script requires a file path and would crash on raw commands.
    if "pre" in workspace_dict and "on_project_start" not in tmuxp_workspace:
        pre_val = workspace_dict["pre"]
        if isinstance(pre_val, list):
            tmuxp_workspace["on_project_start"] = "; ".join(pre_val)
        else:
            tmuxp_workspace["on_project_start"] = pre_val

    # Resolve shell_command_before using tmuxinator's exclusive precedence:
    # rbenv > rvm > pre_tab > pre_window (only ONE is selected)
    _scb_val: str | None = None
    if "rbenv" in workspace_dict:
        _scb_val = "rbenv shell {}".format(workspace_dict["rbenv"])
    elif "rvm" in workspace_dict:
        _scb_val = "rvm use {}".format(workspace_dict["rvm"])
    elif "pre_tab" in workspace_dict:
        _raw = workspace_dict["pre_tab"]
        if isinstance(_raw, list):
            _scb_val = "; ".join(_raw)
        elif isinstance(_raw, str):
            _scb_val = _raw
    elif "pre_window" in workspace_dict:
        _raw = workspace_dict["pre_window"]
        if isinstance(_raw, list):
            _scb_val = "; ".join(_raw)
        elif isinstance(_raw, str):
            _scb_val = _raw

    if _scb_val is not None:
        tmuxp_workspace["shell_command_before"] = [_scb_val]

    _startup_window = workspace_dict.get("startup_window")
    _startup_pane = workspace_dict.get("startup_pane")

    for window_dict in workspace_dict["windows"]:
        for k, v in window_dict.items():
            tmuxp_window: dict[str, t.Any] = {
                "window_name": str(k) if k is not None else k,
            }

            if isinstance(v, str) or v is None:
                tmuxp_window["panes"] = [v]
                tmuxp_workspace["windows"].append(tmuxp_window)
                continue
            if isinstance(v, list):
                tmuxp_window["panes"] = _convert_named_panes(v)
                tmuxp_workspace["windows"].append(tmuxp_window)
                continue

            if "pre" in v:
                tmuxp_window["shell_command_before"] = v["pre"]
            if "panes" in v:
                tmuxp_window["panes"] = _convert_named_panes(v["panes"])
            if "root" in v:
                tmuxp_window["start_directory"] = v["root"]

            if "layout" in v:
                tmuxp_window["layout"] = v["layout"]

            if "synchronize" in v:
                sync = v["synchronize"]
                if sync is True or sync == "before":
                    tmuxp_window.setdefault("options", {})["synchronize-panes"] = "on"
                elif sync == "after":
                    tmuxp_window.setdefault("options_after", {})[
                        "synchronize-panes"
                    ] = "on"

            tmuxp_workspace["windows"].append(tmuxp_window)

    # Post-process startup_window / startup_pane into focus flags
    if _startup_window is not None and tmuxp_workspace["windows"]:
        _matched = False
        for w in tmuxp_workspace["windows"]:
            if w.get("window_name") == str(_startup_window):
                w["focus"] = True
                _matched = True
                break
        if not _matched:
            _idx = _resolve_tmux_list_position(
                _startup_window,
                base_index=base_index,
                item_count=len(tmuxp_workspace["windows"]),
            )
            if _idx is not None:
                tmuxp_workspace["windows"][_idx]["focus"] = True
            else:
                logger.warning(
                    "startup_window %r not found for tmux base-index %d",
                    _startup_window,
                    base_index,
                )

    if _startup_pane is not None and tmuxp_workspace["windows"]:
        _target = next(
            (w for w in tmuxp_workspace["windows"] if w.get("focus")),
            tmuxp_workspace["windows"][0],
        )
        if "panes" in _target:
            _pidx = _resolve_tmux_list_position(
                _startup_pane,
                base_index=pane_base_index,
                item_count=len(_target["panes"]),
            )
            if _pidx is not None:
                _pane = _target["panes"][_pidx]
                if isinstance(_pane, dict):
                    _pane["focus"] = True
                else:
                    _target["panes"][_pidx] = {
                        "shell_command": [_pane] if _pane else [],
                        "focus": True,
                    }
            else:
                logger.warning(
                    "startup_pane %r not found for tmux pane-base-index %d",
                    _startup_pane,
                    pane_base_index,
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
