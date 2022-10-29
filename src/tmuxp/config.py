"""Configuration parsing and export for tmuxp.

tmuxp.config
~~~~~~~~~~~~

"""
import logging
import os
from typing import Dict

from . import exc

logger = logging.getLogger(__name__)


def validate_schema(workspace_dict):
    """
    Return True if config schema is correct.

    Parameters
    ----------
    workspace_dict : dict
        session configuration

    Returns
    -------
    bool
    """
    # verify session_name
    if "session_name" not in workspace_dict:
        raise exc.ConfigError('config requires "session_name"')

    if "windows" not in workspace_dict:
        raise exc.ConfigError('config requires list of "windows"')

    for window in workspace_dict["windows"]:
        if "window_name" not in window:
            raise exc.ConfigError('config window is missing "window_name"')

    if "plugins" in workspace_dict:
        if not isinstance(workspace_dict["plugins"], list):
            raise exc.ConfigError('"plugins" only supports list type')

    return True


def is_workspace_file(filename, extensions=[".yml", ".yaml", ".json"]):
    """
    Return True if file has a valid workspace file type.

    Parameters
    ----------
    filename : str
        filename to check (e.g. ``mysession.json``).
    extensions : str or list
        filetypes to check (e.g. ``['.yaml', '.json']``).

    Returns
    -------
    bool
    """
    extensions = [extensions] if isinstance(extensions, str) else extensions
    return any(filename.endswith(e) for e in extensions)


def in_dir(
    config_dir=os.path.expanduser("~/.tmuxp"), extensions=[".yml", ".yaml", ".json"]
):
    """
    Return a list of configs in ``config_dir``.

    Parameters
    ----------
    config_dir : str
        directory to search
    extensions : list
        filetypes to check (e.g. ``['.yaml', '.json']``).

    Returns
    -------
    list
    """
    configs = []

    for filename in os.listdir(config_dir):
        if is_workspace_file(filename, extensions) and not filename.startswith("."):
            configs.append(filename)

    return configs


def in_cwd():
    """
    Return list of configs in current working directory.

    If filename is ``.tmuxp.py``, ``.tmuxp.json``, ``.tmuxp.yaml``.

    Returns
    -------
    list
        configs in current working directory

    Examples
    --------
    >>> sorted(in_cwd())
    ['.tmuxp.json', '.tmuxp.yaml']
    """
    configs = []

    for filename in os.listdir(os.getcwd()):
        if filename.startswith(".tmuxp") and is_workspace_file(filename):
            configs.append(filename)

    return configs


def expandshell(_path):
    """
    Return expanded path based on user's ``$HOME`` and ``env``.

    :py:func:`os.path.expanduser` and :py:func:`os.path.expandvars`.

    Parameters
    ----------
    path : str
        path to expand

    Returns
    -------
    str
        path with shell variables expanded
    """
    return os.path.expandvars(os.path.expanduser(_path))


def inline(workspace_dict):
    """
    Return config in inline form, opposite of :meth:`config.expand`.

    Parameters
    ----------
    workspace_dict : dict

    Returns
    -------
    dict
        configuration with optional inlined configs.
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

    # recurse into window and pane config items
    if "windows" in workspace_dict:
        workspace_dict["windows"] = [
            inline(window) for window in workspace_dict["windows"]
        ]
    if "panes" in workspace_dict:
        workspace_dict["panes"] = [inline(pane) for pane in workspace_dict["panes"]]

    return workspace_dict


def expand_cmd(p: Dict) -> Dict:
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

        if isinstance(cmds, list) and len(cmds) == int(1):
            if any(a in cmds for a in [None, "blank", "pane"]):
                cmds = []

        for cmd_idx, cmd in enumerate(cmds):
            if isinstance(cmd, str):
                cmds[cmd_idx] = {"cmd": cmd}
            cmds[cmd_idx]["cmd"] = expandshell(cmds[cmd_idx]["cmd"])

        p["shell_command"] = cmds
    else:
        p["shell_command"] = []
    return p


def expand(workspace_dict, cwd=None, parent=None):
    """Return config with shorthand and inline properties expanded.

    This is necessary to keep the code in the :class:`WorkspaceBuilder` clean
    and also allow for neat, short-hand configurations.

    As a simple example, internally, tmuxp expects that config options
    like ``shell_command`` are a list (array)::

        'shell_command': ['htop']

    tmuxp configs allow for it to be simply a string::

        'shell_command': 'htop'

    ConfigReader will load JSON/YAML files into python dicts for you.

    Parameters
    ----------
    workspace_dict : dict
        the configuration for the session
    cwd : str
        directory to expand relative paths against. should be the dir of the
        config directory.
    parent : str
        (used on recursive entries) start_directory of parent window or session
        object.

    Returns
    -------
    dict
    """

    # Note: cli.py will expand configs relative to project's config directory
    # for the first cwd argument.
    if not cwd:
        cwd = os.getcwd()

    if "session_name" in workspace_dict:
        workspace_dict["session_name"] = expandshell(workspace_dict["session_name"])
    if "window_name" in workspace_dict:
        workspace_dict["window_name"] = expandshell(workspace_dict["window_name"])
    if "environment" in workspace_dict:
        for key in workspace_dict["environment"]:
            val = workspace_dict["environment"][key]
            val = expandshell(val)
            if any(val.startswith(a) for a in [".", "./"]):
                val = os.path.normpath(os.path.join(cwd, val))
            workspace_dict["environment"][key] = val
    if "global_options" in workspace_dict:
        for key in workspace_dict["global_options"]:
            val = workspace_dict["global_options"][key]
            if isinstance(val, str):
                val = expandshell(val)
                if any(val.startswith(a) for a in [".", "./"]):
                    val = os.path.normpath(os.path.join(cwd, val))
            workspace_dict["global_options"][key] = val
    if "options" in workspace_dict:
        for key in workspace_dict["options"]:
            val = workspace_dict["options"][key]
            if isinstance(val, str):
                val = expandshell(val)
                if any(val.startswith(a) for a in [".", "./"]):
                    val = os.path.normpath(os.path.join(cwd, val))
            workspace_dict["options"][key] = val

    # Any config section, session, window, pane that can contain the
    # 'shell_command' value
    if "start_directory" in workspace_dict:
        workspace_dict["start_directory"] = expandshell(
            workspace_dict["start_directory"]
        )
        start_path = workspace_dict["start_directory"]
        if any(start_path.startswith(a) for a in [".", "./"]):
            # if window has a session, or pane has a window with a
            # start_directory of . or ./, make sure the start_directory can be
            # relative to the parent.
            #
            # This is for the case where you may be loading a config from
            # outside your shell current directory.
            if parent:
                cwd = parent["start_directory"]
            start_path = os.path.normpath(os.path.join(cwd, start_path))
            workspace_dict["start_directory"] = start_path

    if "before_script" in workspace_dict:
        workspace_dict["before_script"] = expandshell(workspace_dict["before_script"])
        if any(workspace_dict["before_script"].startswith(a) for a in [".", "./"]):
            workspace_dict["before_script"] = os.path.normpath(
                os.path.join(cwd, workspace_dict["before_script"])
            )

    if "shell_command" in workspace_dict and isinstance(
        workspace_dict["shell_command"], str
    ):
        workspace_dict["shell_command"] = [workspace_dict["shell_command"]]

    if "shell_command_before" in workspace_dict:
        shell_command_before = workspace_dict["shell_command_before"]

        workspace_dict["shell_command_before"] = expand_cmd(shell_command_before)

    # recurse into window and pane config items
    if "windows" in workspace_dict:
        workspace_dict["windows"] = [
            expand(window, parent=workspace_dict)
            for window in workspace_dict["windows"]
        ]
    elif "panes" in workspace_dict:
        pane_configs = workspace_dict["panes"]
        for pane_idx, pane_config in enumerate(pane_configs):
            pane_configs[pane_idx] = {}
            pane_configs[pane_idx].update(expand_cmd(pane_config))
        workspace_dict["panes"] = [
            expand(pane, parent=workspace_dict) for pane in pane_configs
        ]

    return workspace_dict


def trickle(workspace_dict):
    """Return a dict with "trickled down" / inherited config values.

    This will only work if config has been expanded to full form with
    :meth:`config.expand`.

    tmuxp allows certain commands to be default at the session, window
    level. shell_command_before trickles down and prepends the
    ``shell_command`` for the pane.

    Parameters
    ----------
    workspace_dict : dict
        the session configuration.

    Returns
    -------
    dict
    """

    # prepends a pane's ``shell_command`` list with the window and sessions'
    # ``shell_command_before``.

    if "start_directory" in workspace_dict:
        session_start_directory = workspace_dict["start_directory"]
    else:
        session_start_directory = None

    if "suppress_history" in workspace_dict:
        suppress_history = workspace_dict["suppress_history"]
    else:
        suppress_history = None

    for window_dict in workspace_dict["windows"]:

        # Prepend start_directory to relative window commands
        if session_start_directory:
            if "start_directory" not in window_dict:
                window_dict["start_directory"] = session_start_directory
            else:
                if not any(
                    window_dict["start_directory"].startswith(a) for a in ["~", "/"]
                ):
                    window_start_path = os.path.join(
                        session_start_directory, window_dict["start_directory"]
                    )
                    window_dict["start_directory"] = window_start_path

        # We only need to trickle to the window, workspace builder checks wconf
        if suppress_history is not None:
            if "suppress_history" not in window_dict:
                window_dict["suppress_history"] = suppress_history

        # If panes were NOT specified for a window, assume that a single pane
        # with no shell commands is desired
        if "panes" not in window_dict:
            window_dict["panes"] = [{"shell_command": []}]

        for pane_idx, pane_config in enumerate(window_dict["panes"]):
            commands_before = []

            # Prepend shell_command_before to commands
            if "shell_command_before" in workspace_dict:
                commands_before.extend(
                    workspace_dict["shell_command_before"]["shell_command"]
                )
            if "shell_command_before" in window_dict:
                commands_before.extend(
                    window_dict["shell_command_before"]["shell_command"]
                )
            if "shell_command_before" in pane_config:
                commands_before.extend(
                    pane_config["shell_command_before"]["shell_command"]
                )

            if "shell_command" in pane_config:
                commands_before.extend(pane_config["shell_command"])

            window_dict["panes"][pane_idx]["shell_command"] = commands_before
            # pane_config['shell_command'] = commands_before

    return workspace_dict


def import_tmuxinator(workspace_dict):
    """Return tmuxp config from a `tmuxinator`_ yaml config.

    .. _tmuxinator: https://github.com/aziz/tmuxinator

    Parameters
    ----------
    workspace_dict : dict
        python dict for session configuration.

    Returns
    -------
    dict
    """

    tmuxp_config = {}

    if "project_name" in workspace_dict:
        tmuxp_config["session_name"] = workspace_dict.pop("project_name")
    elif "name" in workspace_dict:
        tmuxp_config["session_name"] = workspace_dict.pop("name")
    else:
        tmuxp_config["session_name"] = None

    if "project_root" in workspace_dict:
        tmuxp_config["start_directory"] = workspace_dict.pop("project_root")
    elif "root" in workspace_dict:
        tmuxp_config["start_directory"] = workspace_dict.pop("root")

    if "cli_args" in workspace_dict:
        tmuxp_config["config"] = workspace_dict["cli_args"]

        if "-f" in tmuxp_config["config"]:
            tmuxp_config["config"] = tmuxp_config["config"].replace("-f", "").strip()
    elif "tmux_options" in workspace_dict:
        tmuxp_config["config"] = workspace_dict["tmux_options"]

        if "-f" in tmuxp_config["config"]:
            tmuxp_config["config"] = tmuxp_config["config"].replace("-f", "").strip()

    if "socket_name" in workspace_dict:
        tmuxp_config["socket_name"] = workspace_dict["socket_name"]

    tmuxp_config["windows"] = []

    if "tabs" in workspace_dict:
        workspace_dict["windows"] = workspace_dict.pop("tabs")

    if "pre" in workspace_dict and "pre_window" in workspace_dict:
        tmuxp_config["shell_command"] = workspace_dict["pre"]

        if isinstance(workspace_dict["pre"], str):
            tmuxp_config["shell_command_before"] = [workspace_dict["pre_window"]]
        else:
            tmuxp_config["shell_command_before"] = workspace_dict["pre_window"]
    elif "pre" in workspace_dict:
        if isinstance(workspace_dict["pre"], str):
            tmuxp_config["shell_command_before"] = [workspace_dict["pre"]]
        else:
            tmuxp_config["shell_command_before"] = workspace_dict["pre"]

    if "rbenv" in workspace_dict:
        if "shell_command_before" not in tmuxp_config:
            tmuxp_config["shell_command_before"] = []
        tmuxp_config["shell_command_before"].append(
            "rbenv shell %s" % workspace_dict["rbenv"]
        )

    for window_dict in workspace_dict["windows"]:
        for k, v in window_dict.items():
            window_dict = {"window_name": k}

            if isinstance(v, str) or v is None:
                window_dict["panes"] = [v]
                tmuxp_config["windows"].append(window_dict)
                continue
            elif isinstance(v, list):
                window_dict["panes"] = v
                tmuxp_config["windows"].append(window_dict)
                continue

            if "pre" in v:
                window_dict["shell_command_before"] = v["pre"]
            if "panes" in v:
                window_dict["panes"] = v["panes"]
            if "root" in v:
                window_dict["start_directory"] = v["root"]

            if "layout" in v:
                window_dict["layout"] = v["layout"]
            tmuxp_config["windows"].append(window_dict)
    return tmuxp_config


def import_teamocil(workspace_dict):
    """Return tmuxp config from a `teamocil`_ yaml config.

    .. _teamocil: https://github.com/remiprev/teamocil

    Parameters
    ----------
    workspace_dict : dict
        python dict for session configuration

    Notes
    -----

    Todos:

    - change  'root' to a cd or start_directory
    - width in pane -> main-pain-width
    - with_env_var
    - clear
    - cmd_separator
    """

    tmuxp_config = {}

    if "session" in workspace_dict:
        workspace_dict = workspace_dict["session"]

    if "name" in workspace_dict:
        tmuxp_config["session_name"] = workspace_dict["name"]
    else:
        tmuxp_config["session_name"] = None

    if "root" in workspace_dict:
        tmuxp_config["start_directory"] = workspace_dict.pop("root")

    tmuxp_config["windows"] = []

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
        tmuxp_config["windows"].append(window_dict)

    return tmuxp_config
