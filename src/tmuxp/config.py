"""Configuration parsing and export for tmuxp.

tmuxp.config
~~~~~~~~~~~~

"""
import logging
import os
from typing import Dict

from . import exc

logger = logging.getLogger(__name__)


def validate_schema(session_config):
    """
    Return True if config schema is correct.

    Parameters
    ----------
    session_config : dict
        session configuration

    Returns
    -------
    bool
    """

    # verify session_name
    if "session_name" not in session_config:
        raise exc.ConfigError('config requires "session_name"')

    if "windows" not in session_config:
        raise exc.ConfigError('config requires list of "windows"')

    for window in session_config["windows"]:
        if "window_name" not in window:
            raise exc.ConfigError('config window is missing "window_name"')

    if "plugins" in session_config:
        if not isinstance(session_config["plugins"], list):
            raise exc.ConfigError('"plugins" only supports list type')

    return True


def is_config_file(filename, extensions=[".yml", ".yaml", ".json"]):
    """
    Return True if file has a valid config file type.

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
        if is_config_file(filename, extensions) and not filename.startswith("."):
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
        if filename.startswith(".tmuxp") and is_config_file(filename):
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


def inline(session_config):
    """
    Return config in inline form, opposite of :meth:`config.expand`.

    Parameters
    ----------
    session_config : dict

    Returns
    -------
    dict
        configuration with optional inlined configs.
    """

    if (
        "shell_command" in session_config
        and isinstance(session_config["shell_command"], list)
        and len(session_config["shell_command"]) == 1
    ):
        session_config["shell_command"] = session_config["shell_command"][0]

        if len(session_config.keys()) == int(1):
            session_config = session_config["shell_command"]
    if (
        "shell_command_before" in session_config
        and isinstance(session_config["shell_command_before"], list)
        and len(session_config["shell_command_before"]) == 1
    ):
        session_config["shell_command_before"] = session_config["shell_command_before"][
            0
        ]

    # recurse into window and pane config items
    if "windows" in session_config:
        session_config["windows"] = [
            inline(window) for window in session_config["windows"]
        ]
    if "panes" in session_config:
        session_config["panes"] = [inline(pane) for pane in session_config["panes"]]

    return session_config


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


def expand(session_config, cwd=None, parent=None):
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
    session_config : dict
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

    if "session_name" in session_config:
        session_config["session_name"] = expandshell(session_config["session_name"])
    if "window_name" in session_config:
        session_config["window_name"] = expandshell(session_config["window_name"])
    if "environment" in session_config:
        for key in session_config["environment"]:
            val = session_config["environment"][key]
            val = expandshell(val)
            if any(val.startswith(a) for a in [".", "./"]):
                val = os.path.normpath(os.path.join(cwd, val))
            session_config["environment"][key] = val
    if "global_options" in session_config:
        for key in session_config["global_options"]:
            val = session_config["global_options"][key]
            if isinstance(val, str):
                val = expandshell(val)
                if any(val.startswith(a) for a in [".", "./"]):
                    val = os.path.normpath(os.path.join(cwd, val))
            session_config["global_options"][key] = val
    if "options" in session_config:
        for key in session_config["options"]:
            val = session_config["options"][key]
            if isinstance(val, str):
                val = expandshell(val)
                if any(val.startswith(a) for a in [".", "./"]):
                    val = os.path.normpath(os.path.join(cwd, val))
            session_config["options"][key] = val

    # Any config section, session, window, pane that can contain the
    # 'shell_command' value
    if "start_directory" in session_config:
        session_config["start_directory"] = expandshell(
            session_config["start_directory"]
        )
        start_path = session_config["start_directory"]
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
            session_config["start_directory"] = start_path

    if "before_script" in session_config:
        session_config["before_script"] = expandshell(session_config["before_script"])
        if any(session_config["before_script"].startswith(a) for a in [".", "./"]):
            session_config["before_script"] = os.path.normpath(
                os.path.join(cwd, session_config["before_script"])
            )

    if "shell_command" in session_config and isinstance(
        session_config["shell_command"], str
    ):
        session_config["shell_command"] = [session_config["shell_command"]]

    if "shell_command_before" in session_config:
        shell_command_before = session_config["shell_command_before"]

        session_config["shell_command_before"] = expand_cmd(shell_command_before)

    # recurse into window and pane config items
    if "windows" in session_config:
        session_config["windows"] = [
            expand(window, parent=session_config)
            for window in session_config["windows"]
        ]
    elif "panes" in session_config:
        pane_configs = session_config["panes"]
        for pane_idx, pane_config in enumerate(pane_configs):
            pane_configs[pane_idx] = {}
            pane_configs[pane_idx].update(expand_cmd(pane_config))
        session_config["panes"] = [
            expand(pane, parent=session_config) for pane in pane_configs
        ]

    return session_config


def trickle(session_config):
    """Return a dict with "trickled down" / inherited config values.

    This will only work if config has been expanded to full form with
    :meth:`config.expand`.

    tmuxp allows certain commands to be default at the session, window
    level. shell_command_before trickles down and prepends the
    ``shell_command`` for the pane.

    Parameters
    ----------
    session_config : dict
        the session configuration.

    Returns
    -------
    dict
    """

    # prepends a pane's ``shell_command`` list with the window and sessions'
    # ``shell_command_before``.

    if "start_directory" in session_config:
        session_start_directory = session_config["start_directory"]
    else:
        session_start_directory = None

    if "suppress_history" in session_config:
        suppress_history = session_config["suppress_history"]
    else:
        suppress_history = None

    for window_config in session_config["windows"]:

        # Prepend start_directory to relative window commands
        if session_start_directory:
            if "start_directory" not in window_config:
                window_config["start_directory"] = session_start_directory
            else:
                if not any(
                    window_config["start_directory"].startswith(a) for a in ["~", "/"]
                ):
                    window_start_path = os.path.join(
                        session_start_directory, window_config["start_directory"]
                    )
                    window_config["start_directory"] = window_start_path

        # We only need to trickle to the window, workspace builder checks wconf
        if suppress_history is not None:
            if "suppress_history" not in window_config:
                window_config["suppress_history"] = suppress_history

        # If panes were NOT specified for a window, assume that a single pane
        # with no shell commands is desired
        if "panes" not in window_config:
            window_config["panes"] = [{"shell_command": []}]

        for pane_idx, pane_config in enumerate(window_config["panes"]):
            commands_before = []

            # Prepend shell_command_before to commands
            if "shell_command_before" in session_config:
                commands_before.extend(
                    session_config["shell_command_before"]["shell_command"]
                )
            if "shell_command_before" in window_config:
                commands_before.extend(
                    window_config["shell_command_before"]["shell_command"]
                )
            if "shell_command_before" in pane_config:
                commands_before.extend(
                    pane_config["shell_command_before"]["shell_command"]
                )

            if "shell_command" in pane_config:
                commands_before.extend(pane_config["shell_command"])

            window_config["panes"][pane_idx]["shell_command"] = commands_before
            # pane_config['shell_command'] = commands_before

    return session_config


def import_tmuxinator(session_config):
    """Return tmuxp config from a `tmuxinator`_ yaml config.

    .. _tmuxinator: https://github.com/aziz/tmuxinator

    Parameters
    ----------
    session_config : dict
        python dict for session configuration.

    Returns
    -------
    dict
    """

    tmuxp_config = {}

    if "project_name" in session_config:
        tmuxp_config["session_name"] = session_config.pop("project_name")
    elif "name" in session_config:
        tmuxp_config["session_name"] = session_config.pop("name")
    else:
        tmuxp_config["session_name"] = None

    if "project_root" in session_config:
        tmuxp_config["start_directory"] = session_config.pop("project_root")
    elif "root" in session_config:
        tmuxp_config["start_directory"] = session_config.pop("root")

    if "cli_args" in session_config:
        tmuxp_config["config"] = session_config["cli_args"]

        if "-f" in tmuxp_config["config"]:
            tmuxp_config["config"] = tmuxp_config["config"].replace("-f", "").strip()
    elif "tmux_options" in session_config:
        tmuxp_config["config"] = session_config["tmux_options"]

        if "-f" in tmuxp_config["config"]:
            tmuxp_config["config"] = tmuxp_config["config"].replace("-f", "").strip()

    if "socket_name" in session_config:
        tmuxp_config["socket_name"] = session_config["socket_name"]

    tmuxp_config["windows"] = []

    if "tabs" in session_config:
        session_config["windows"] = session_config.pop("tabs")

    if "pre" in session_config and "pre_window" in session_config:
        tmuxp_config["shell_command"] = session_config["pre"]

        if isinstance(session_config["pre"], str):
            tmuxp_config["shell_command_before"] = [session_config["pre_window"]]
        else:
            tmuxp_config["shell_command_before"] = session_config["pre_window"]
    elif "pre" in session_config:
        if isinstance(session_config["pre"], str):
            tmuxp_config["shell_command_before"] = [session_config["pre"]]
        else:
            tmuxp_config["shell_command_before"] = session_config["pre"]

    if "rbenv" in session_config:
        if "shell_command_before" not in tmuxp_config:
            tmuxp_config["shell_command_before"] = []
        tmuxp_config["shell_command_before"].append(
            "rbenv shell %s" % session_config["rbenv"]
        )

    for window_config in session_config["windows"]:
        for k, v in window_config.items():
            window_config = {"window_name": k}

            if isinstance(v, str) or v is None:
                window_config["panes"] = [v]
                tmuxp_config["windows"].append(window_config)
                continue
            elif isinstance(v, list):
                window_config["panes"] = v
                tmuxp_config["windows"].append(window_config)
                continue

            if "pre" in v:
                window_config["shell_command_before"] = v["pre"]
            if "panes" in v:
                window_config["panes"] = v["panes"]
            if "root" in v:
                window_config["start_directory"] = v["root"]

            if "layout" in v:
                window_config["layout"] = v["layout"]
            tmuxp_config["windows"].append(window_config)
    return tmuxp_config


def import_teamocil(session_config):
    """Return tmuxp config from a `teamocil`_ yaml config.

    .. _teamocil: https://github.com/remiprev/teamocil

    Parameters
    ----------
    session_config : dict
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

    if "session" in session_config:
        session_config = session_config["session"]

    if "name" in session_config:
        tmuxp_config["session_name"] = session_config["name"]
    else:
        tmuxp_config["session_name"] = None

    if "root" in session_config:
        tmuxp_config["start_directory"] = session_config.pop("root")

    tmuxp_config["windows"] = []

    for w in session_config["windows"]:

        windowdict = {"window_name": w["name"]}

        if "clear" in w:
            windowdict["clear"] = w["clear"]

        if "filters" in w:
            if "before" in w["filters"]:
                for b in w["filters"]["before"]:
                    windowdict["shell_command_before"] = w["filters"]["before"]
            if "after" in w["filters"]:
                for b in w["filters"]["after"]:
                    windowdict["shell_command_after"] = w["filters"]["after"]

        if "root" in w:
            windowdict["start_directory"] = w.pop("root")

        if "splits" in w:
            w["panes"] = w.pop("splits")

        if "panes" in w:
            for p in w["panes"]:
                if "cmd" in p:
                    p["shell_command"] = p.pop("cmd")
                if "width" in p:
                    # todo support for height/width
                    p.pop("width")
            windowdict["panes"] = w["panes"]

        if "layout" in w:
            windowdict["layout"] = w["layout"]
        tmuxp_config["windows"].append(windowdict)

    return tmuxp_config
