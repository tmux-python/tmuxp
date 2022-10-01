"""Command line tool for managing tmux workspaces and tmuxp configurations.

tmuxp.cli
~~~~~~~~~

"""
import importlib
import logging
import os
import pathlib
import shutil
import sys
from typing import List

import click

from libtmux.common import has_gte_version
from libtmux.server import Server
from tmuxp import config_reader

from .. import config, exc, log, util
from ..workspacebuilder import WorkspaceBuilder
from .utils import ConfigPath, _validate_choices, get_config_dir, tmuxp_echo


def set_layout_hook(session, hook_name):
    """Set layout hooks to normalize layout.

    References:

        - tmuxp issue: https://github.com/tmux-python/tmuxp/issues/309
        - tmux issue: https://github.com/tmux/tmux/issues/1106

    tmux 2.6+ requires that the window be viewed with the client before
    select-layout adjustments can take effect.

    To handle this, this function creates temporary hook for this session to
    iterate through all windows and select the layout.

    In order for layout changes to take effect, a client must at the very
    least be attached to the window (not just the session).

    hook_name is provided to allow this to set to multiple scenarios, such
    as 'client-attached' (which the user attaches the session). You may
    also want 'after-switch-client' for cases where the user loads tmuxp
    sessions inside tmux since tmuxp offers to switch for them.

    Also, the hooks are set immediately unbind after they're invoked via -u.

    Parameters
    ----------
    session : :class:`libtmux.session.Session`
        session to bind hook to
    hook_name : str
        hook name to bind to, e.g. 'client-attached'
    """
    cmd = ["set-hook", "-t", session.id, hook_name]
    hook_cmd = []
    attached_window = session.attached_window
    for window in session.windows:
        # unfortunately, select-layout won't work unless
        # we've literally selected the window at least once
        # with the client
        hook_cmd.append(f"selectw -t {window.id}")
        # edit: removed -t, or else it won't respect main-pane-w/h
        hook_cmd.append("selectl")
        hook_cmd.append("selectw -p")

    # unset the hook immediately after executing
    hook_cmd.append(
        "set-hook -u -t {target_session} {hook_name}".format(
            target_session=session.id, hook_name=hook_name
        )
    )
    hook_cmd.append(f"selectw -t {attached_window.id}")

    # join the hook's commands with semicolons
    hook_cmd = "{}".format("; ".join(hook_cmd))

    # append the hook command
    cmd.append(hook_cmd)

    # create the hook
    session.cmd(*cmd)


def load_plugins(sconf):
    """
    Load and return plugins in config
    """
    plugins = []
    if "plugins" in sconf:
        for plugin in sconf["plugins"]:
            try:
                module_name = plugin.split(".")
                module_name = ".".join(module_name[:-1])
                plugin_name = plugin.split(".")[-1]
                plugin = getattr(importlib.import_module(module_name), plugin_name)
                plugins.append(plugin())
            except exc.TmuxpPluginException as error:
                if not click.confirm(
                    "%sSkip loading %s?"
                    % (click.style(str(error), fg="yellow"), plugin_name),
                    default=True,
                ):
                    click.echo(
                        click.style("[Not Skipping] ", fg="yellow")
                        + "Plugin versions constraint not met. Exiting..."
                    )
                    sys.exit(1)
            except Exception as error:
                click.echo(
                    click.style("[Plugin Error] ", fg="red")
                    + f"Couldn't load {plugin}\n"
                    + click.style(f"{error}", fg="yellow")
                )
                sys.exit(1)

    return plugins


def _reattach(builder):
    """
    Reattach session (depending on env being inside tmux already or not)

    Parameters
    ----------
    builder: :class:`workspacebuilder.WorkspaceBuilder`

    Notes
    -----
    If ``TMUX`` environmental variable exists in the environment this script is
    running, that means we're in a tmux client. So ``tmux switch-client`` will
    load the session.

    If not, ``tmux attach-session`` loads the client to the target session.
    """
    for plugin in builder.plugins:
        plugin.reattach(builder.session)
        proc = builder.session.cmd("display-message", "-p", "'#S'")
        for line in proc.stdout:
            print(line)

    if "TMUX" in os.environ:
        builder.session.switch_client()

    else:
        builder.session.attach_session()


def _load_attached(builder, detached):
    """
    Load config in new session

    Parameters
    ----------
    builder: :class:`workspacebuilder.WorkspaceBuilder`
    detached : bool
    """
    builder.build()

    if "TMUX" in os.environ:  # tmuxp ran from inside tmux
        # unset TMUX, save it, e.g. '/tmp/tmux-1000/default,30668,0'
        tmux_env = os.environ.pop("TMUX")

        if has_gte_version("2.6"):
            set_layout_hook(builder.session, "client-session-changed")

        builder.session.switch_client()  # switch client to new session

        os.environ["TMUX"] = tmux_env  # set TMUX back again
    else:
        if has_gte_version("2.6"):
            # if attaching for first time
            set_layout_hook(builder.session, "client-attached")

            # for cases where user switches client for first time
            set_layout_hook(builder.session, "client-session-changed")

        if not detached:
            builder.session.attach_session()


def _load_detached(builder):
    """
    Load config in new session but don't attach

    Parameters
    ----------
    builder: :class:`workspacebuilder.WorkspaceBuilder`
    """
    builder.build()

    if has_gte_version("2.6"):  # prepare for both cases
        set_layout_hook(builder.session, "client-attached")
        set_layout_hook(builder.session, "client-session-changed")

    print("Session created in detached state.")


def _load_append_windows_to_current_session(builder):
    """
    Load config as new windows in current session

    Parameters
    ----------
    builder: :class:`workspacebuilder.WorkspaceBuilder`
    """
    current_attached_session = builder.find_current_attached_session()
    builder.build(current_attached_session, append=True)
    if has_gte_version("2.6"):  # prepare for both cases
        set_layout_hook(builder.session, "client-attached")
        set_layout_hook(builder.session, "client-session-changed")


def _setup_plugins(builder):
    """
    Runs after before_script

    Parameters
    ----------
    builder: :class:`workspacebuilder.WorkspaceBuilder`
    """
    for plugin in builder.plugins:
        plugin.before_script(builder.session)

    return builder.session


def load_workspace(
    config_file,
    socket_name=None,
    socket_path=None,
    tmux_config_file=None,
    new_session_name=None,
    colors=None,
    detached=False,
    answer_yes=False,
    append=False,
):
    """
    Load a tmux "workspace" session via tmuxp file.

    Parameters
    ----------
    config_file : str
        absolute path to config file
    socket_name : str, optional
        ``tmux -L <socket-name>``
    socket_path: str, optional
        ``tmux -S <socket-path>``
    new_session_name: str, options
        ``tmux new -s <new_session_name>``
    colors : str, optional
        '-2'
            Force tmux to support 256 colors
    detached : bool
        Force detached state. default False.
    answer_yes : bool
        Assume yes when given prompt to attach in new session.
        Default False.
    append : bool
       Assume current when given prompt to append windows in same session.
       Default False.

    Notes
    -----

    tmuxp will check and load a configuration file. The file will use ConfigReader
    to load a JSON/YAML into a :py:obj:`dict`. Then :func:`config.expand` and
    :func:`config.trickle` will be used to expand any shorthands, template
    variables, or file paths relative to where the config/script is executed
    from.

    :func:`config.expand` accepts the directory of the config file, so the
    user's configuration can resolve absolute paths relative to where the
    config file is. In otherwords, if a config file at */var/moo/hi.yaml*
    has *./* in its configs, we want to be sure any file path with *./* is
    relative to */var/moo*, not the user's PWD.

    A :class:`libtmux.Server` object is created. No tmux server is started yet,
    just the object.

    The prepared configuration and the server object is passed into an instance
    of :class:`~tmuxp.workspacebuilder.WorkspaceBuilder`.

    A sanity check against :meth:`libtmux.common.which` is ran. It will raise
    an exception if tmux isn't found.

    If a tmux session under the same name as ``session_name`` in the tmuxp
    configuration exists, tmuxp offers to attach the session. Currently, tmuxp
    does not allow appending a workspace / incremental building on top of a
    current session (pull requests are welcome!).

    :meth:`~tmuxp.workspacebuilder.WorkspaceBuilder.build` will build the session in
    the background via using tmux's detached state (``-d``).

    After the session (workspace) is built, unless the user decided to load
    the session in the background via ``tmuxp -d`` (which is in the spirit
    of tmux's ``-d``), we need to prompt the user to attach the session.

    If the user is already inside a tmux client, which we detect via the
    ``TMUX`` environment variable bring present, we will prompt the user to
    switch their current client to it.

    If they're outside of tmux client - in a plain-old PTY - we will
    automatically ``attach``.

    If an exception is raised during the building of the workspace, tmuxp will
    prompt to cleanup (``$ tmux kill-session``) the session on the user's
    behalf. An exception raised during this process means it's not easy to
    predict how broken the session is.

    .. versionchanged:: tmux 2.6+

        In tmux 2.6, the way layout and proportion's work when interfacing
        with tmux in a detached state (outside of a client) changed. Since
        tmuxp builds workspaces in a detached state, the WorkspaceBuilder isn't
        able to rely on functionality requiring awarness of session geometry,
        e.g. ``set-layout``.

        Thankfully, tmux is able to defer commands to run after the user
        performs certain actions, such as loading a client via
        ``attach-session`` or ``switch-client``.

        Upon client switch, ``client-session-changed`` is triggered [1]_.

    References
    ----------
    .. [1] cmd-switch-client.c hook. GitHub repo for tmux.

       https://github.com/tmux/tmux/blob/2.6/cmd-switch-client.c#L132.
       Accessed April 8th, 2018.
    """
    # get the canonical path, eliminating any symlinks
    if isinstance(config_file, str):
        config_file = pathlib.Path(config_file)

    tmuxp_echo(
        click.style("[Loading] ", fg="green")
        + click.style(str(config_file), fg="blue", bold=True)
    )

    # ConfigReader allows us to open a yaml or json file as a dict
    raw_config = config_reader.ConfigReader._from_file(config_file)
    # shapes configurations relative to config / profile file location
    sconfig = config.expand(raw_config, cwd=os.path.dirname(config_file))
    # Overwrite session name
    if new_session_name:
        sconfig["session_name"] = new_session_name
    # propagate config inheritance (e.g. session -> window, window -> pane)
    sconfig = config.trickle(sconfig)

    t = Server(  # create tmux server object
        socket_name=socket_name,
        socket_path=socket_path,
        config_file=tmux_config_file,
        colors=colors,
    )

    shutil.which("tmux")  # raise exception if tmux not found

    try:  # load WorkspaceBuilder object for tmuxp config / tmux server
        builder = WorkspaceBuilder(
            sconf=sconfig, plugins=load_plugins(sconfig), server=t
        )
    except exc.EmptyConfigException:
        tmuxp_echo("%s is empty or parsed no config data" % config_file, err=True)
        return

    session_name = sconfig["session_name"]

    # if the session already exists, prompt the user to attach
    if builder.session_exists(session_name) and not append:
        if not detached and (
            answer_yes
            or click.confirm(
                "%s is already running. Attach?"
                % click.style(session_name, fg="green"),
                default=True,
            )
        ):
            _reattach(builder)
        return

    try:
        if detached:
            _load_detached(builder)
            return _setup_plugins(builder)

        if append:
            if "TMUX" in os.environ:  # tmuxp ran from inside tmux
                _load_append_windows_to_current_session(builder)
            else:
                _load_attached(builder, detached)

            return _setup_plugins(builder)

        # append and answer_yes have no meaning if specified together
        elif answer_yes:
            _load_attached(builder, detached)
            return _setup_plugins(builder)

        if "TMUX" in os.environ:  # tmuxp ran from inside tmux
            msg = (
                "Already inside TMUX, switch to session? yes/no\n"
                "Or (a)ppend windows in the current active session?\n[y/n/a]"
            )
            options = ["y", "n", "a"]
            choice = click.prompt(msg, value_proc=_validate_choices(options))

            if choice == "y":
                _load_attached(builder, detached)
            elif choice == "a":
                _load_append_windows_to_current_session(builder)
            else:
                _load_detached(builder)
        else:
            _load_attached(builder, detached)

    except exc.TmuxpException as e:
        import traceback

        tmuxp_echo(traceback.format_exc(), err=True)
        tmuxp_echo(e, err=True)

        choice = click.prompt(
            "Error loading workspace. (k)ill, (a)ttach, (d)etach?",
            value_proc=_validate_choices(["k", "a", "d"]),
            default="k",
        )

        if choice == "k":
            builder.session.kill_session()
            tmuxp_echo("Session killed.")
        elif choice == "a":
            _reattach(builder)
        else:
            sys.exit()

    return _setup_plugins(builder)


def config_file_completion(ctx, params, incomplete):
    config_dir = pathlib.Path(get_config_dir())
    choices: List[pathlib.Path] = []

    # CWD Paths
    choices += sorted(
        pathlib.Path(os.path.relpath(p, pathlib.Path.cwd()))
        for p in [pathlib.Path.cwd(), *pathlib.Path.cwd().parents]
        if config.in_dir(str(p)) or len(list(p.glob(".tmuxp.*")))
    )
    # CWD look one directory up
    choices += [
        pathlib.Path(f"./{os.path.relpath(p, pathlib.Path.cwd())}")
        for p in pathlib.Path.cwd().glob("*/.tmuxp.*")
    ]

    # Project configs
    choices += sorted((config_dir / c).stem for c in config.in_dir(str(config_dir)))

    return sorted(str(c) for c in choices if str(c).startswith(incomplete))


@click.command(name="load", short_help="Load tmuxp workspaces.")
@click.pass_context
@click.argument(
    "config",
    type=ConfigPath(exists=True),
    nargs=-1,
    shell_complete=config_file_completion,
)
@click.option("-S", "socket_path", help="pass-through for tmux -S")
@click.option("-L", "socket_name", help="pass-through for tmux -L")
@click.option("-f", "tmux_config_file", help="pass-through for tmux -f")
@click.option("-s", "new_session_name", help="start new session with new session name")
@click.option("--yes", "-y", "answer_yes", help="yes", is_flag=True)
@click.option(
    "-d", "detached", help="Load the session without attaching it", is_flag=True
)
@click.option(
    "-a",
    "append",
    help="Load configuration, appending windows to the current session",
    is_flag=True,
)
@click.option(
    "colors",
    "-2",
    flag_value=256,
    default=True,
    help="Force tmux to assume the terminal supports 256 colours.",
)
@click.option(
    "colors",
    "-8",
    flag_value=88,
    help="Like -2, but indicates that the terminal supports 88 colours.",
)
@click.option("--log-file", help="File to log errors/output to")
def command_load(
    ctx,
    config,
    socket_name,
    socket_path,
    tmux_config_file,
    new_session_name,
    answer_yes,
    detached,
    append,
    colors,
    log_file,
):
    """Load a tmux workspace from each CONFIG.

    CONFIG is a specifier for a configuration file.

    If CONFIG is a path to a directory, tmuxp will search it for
    ".tmuxp.{yaml,yml,json}".

    If CONFIG is has no directory component and only a filename, e.g.
    "myconfig.yaml", tmuxp will search the users's config directory for that
    file.

    If CONFIG has no directory component, and only a name with no extension,
    e.g. "myconfig", tmuxp will search the users's config directory for any
    file with the extension ".yaml", ".yml", or ".json" that matches that name.

    If multiple configuration files that match a given CONFIG are found, tmuxp
    will warn and pick the first one found.

    If multiple CONFIGs are provided, workspaces will be created for all of
    them. The last one provided will be attached. The others will be created in
    detached mode.
    """
    util.oh_my_zsh_auto_title()

    if log_file:
        logfile_handler = logging.FileHandler(log_file)
        logfile_handler.setFormatter(log.LogFormatter())
        from . import logger

        logger.addHandler(logfile_handler)

    tmux_options = {
        "socket_name": socket_name,
        "socket_path": socket_path,
        "tmux_config_file": tmux_config_file,
        "new_session_name": new_session_name,
        "answer_yes": answer_yes,
        "colors": colors,
        "detached": detached,
        "append": append,
    }

    if not config:
        tmuxp_echo("Enter at least one CONFIG")
        tmuxp_echo(ctx.get_help(), color=ctx.color)
        ctx.exit()

    if isinstance(config, str):
        load_workspace(config, **tmux_options)

    elif isinstance(config, tuple):
        config = list(config)
        # Load each configuration but the last to the background
        for cfg in config[:-1]:
            opt = tmux_options.copy()
            opt.update({"detached": True, "new_session_name": None})
            load_workspace(cfg, **opt)

        # todo: obey the -d in the cli args only if user specifies
        load_workspace(config[-1], **tmux_options)
