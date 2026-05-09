"""Configuration import adapters to load teamocil, tmuxinator, etc. in tmuxp."""

from __future__ import annotations

import logging
import shlex
import typing as t

logger = logging.getLogger(__name__)


_SHELL_METACHAR_TOKENS = ("|", "&&", "||", ">", "<", "$(", "`", ";")


def _has_shell_metachars(value: t.Any) -> bool:
    """Return True if value contains shell metacharacters that need a real shell.

    tmuxp's `before_script` runs via `subprocess.Popen` after `shlex.split()` —
    no shell process. Pipes, redirects, command substitution, and `&&` chains
    don't work. This helper flags such values so the caller can warn the user.

    Strings, lists of strings, and dicts containing strings are scanned. Any
    other type returns False (nothing to scan).

    >>> _has_shell_metachars("plain command")
    False
    >>> _has_shell_metachars("echo a | grep b")
    True
    >>> _has_shell_metachars(["safe", "echo $(date)"])
    True
    >>> _has_shell_metachars(None)
    False
    """
    if isinstance(value, str):
        return any(token in value for token in _SHELL_METACHAR_TOKENS)
    if isinstance(value, list):
        return any(_has_shell_metachars(item) for item in value)
    return False


def _parse_tmuxinator_tmux_args(
    args_str: str,
    target: dict[str, t.Any],
    session_name: str | None,
) -> None:
    """Parse tmuxinator `cli_args`/`tmux_options` into individual tmux flags.

    Splits via `shlex` and walks tokens to extract `-f` (config), `-L`
    (socket name), and `-S` (socket path). Unknown flags are warned.
    Mutates ``target`` in place.
    """
    mapping = {"-f": "config", "-L": "socket_name", "-S": "socket_path"}
    tokens = shlex.split(args_str)
    i = 0
    while i < len(tokens):
        flag = tokens[i]
        if flag in mapping:
            if i + 1 < len(tokens):
                target[mapping[flag]] = tokens[i + 1]
                i += 2
            else:
                logger.warning(
                    "tmux flag requires a value but none was provided",
                    extra={"tmux_key": flag, "tmux_session": session_name},
                )
                i += 1
        else:
            logger.warning(
                "unrecognized tmux flag in cli_args/tmux_options",
                extra={"tmux_key": flag, "tmux_session": session_name},
            )
            i += 1


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

    args_str = workspace_dict.get("cli_args") or workspace_dict.get("tmux_options")
    if args_str:
        _parse_tmuxinator_tmux_args(
            args_str,
            tmuxp_workspace,
            tmuxp_workspace.get("session_name"),
        )

    if "socket_name" in workspace_dict:
        tmuxp_workspace["socket_name"] = workspace_dict["socket_name"]

    tmuxp_workspace["windows"] = []

    if "tabs" in workspace_dict:
        workspace_dict["windows"] = workspace_dict.pop("tabs")

    if "pre" in workspace_dict:
        pre_value = workspace_dict["pre"]
        if _has_shell_metachars(pre_value):
            logger.warning(
                "pre contains shell constructs that will not work in "
                "before_script (runs without shell=True)",
                extra={
                    "tmux_key": "pre",
                    "tmux_session": tmuxp_workspace.get("session_name"),
                },
            )
        tmuxp_workspace["before_script"] = pre_value

    if "pre_window" in workspace_dict:
        pre_window = workspace_dict["pre_window"]
        tmuxp_workspace["shell_command_before"] = (
            [pre_window] if isinstance(pre_window, str) else pre_window
        )

    if "rbenv" in workspace_dict:
        if "shell_command_before" not in tmuxp_workspace:
            tmuxp_workspace["shell_command_before"] = []
        tmuxp_workspace["shell_command_before"].append(
            "rbenv shell {}".format(workspace_dict["rbenv"]),
        )

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
            if "before" in w["filters"]:
                window_dict["shell_command_before"] = w["filters"]["before"]
            if "after" in w["filters"]:
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
