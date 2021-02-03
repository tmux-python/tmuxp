# -*- coding: utf-8 -*-
"""Command line tool for managing tmux workspaces and tmuxp configurations.

tmuxp.cli
~~~~~~~~~

"""
from __future__ import absolute_import

import importlib
import logging
import os
import platform
import sys

import click
import kaptan
from click.exceptions import FileError

from libtmux.common import (
    has_gte_version,
    has_minimum_version,
    which,
    get_version,
    tmux_cmd,
)
from libtmux.exc import TmuxCommandNotFound
from libtmux.server import Server

from libtmux import __version__ as libtmux_version

from . import config, exc, log, util, __file__ as tmuxp_path
from .__about__ import __version__
from ._compat import PY3, PYMINOR, string_types
from .workspacebuilder import WorkspaceBuilder, freeze

logger = logging.getLogger(__name__)

VALID_CONFIG_DIR_FILE_EXTENSIONS = ['.yaml', '.yml', '.json']


def get_cwd():
    return os.getcwd()


def tmuxp_echo(message=None, log_level='INFO', style_log=False, **click_kwargs):
    """
    Combines logging.log and click.echo
    """
    if style_log:
        logger.log(log.LOG_LEVELS[log_level], message)
    else:
        logger.log(log.LOG_LEVELS[log_level], click.unstyle(message))

    click.echo(message, **click_kwargs)


def get_config_dir():
    """
    Return tmuxp configuration directory.

    ``TMUXP_CONFIGDIR`` environmental variable has precedence if set. We also
    evaluate XDG default directory from XDG_CONFIG_HOME environmental variable
    if set or its default. Then the old default ~/.tmuxp is returned for
    compatibility.

    Returns
    -------
    str :
        absolute path to tmuxp config directory
    """

    paths = []
    if 'TMUXP_CONFIGDIR' in os.environ:
        paths.append(os.environ['TMUXP_CONFIGDIR'])
    if 'XDG_CONFIG_HOME' in os.environ:
        paths.append(os.path.join(os.environ['XDG_CONFIG_HOME'], 'tmuxp'))
    else:
        paths.append('~/.config/tmuxp/')
    paths.append('~/.tmuxp')

    for path in paths:
        path = os.path.expanduser(path)
        if os.path.isdir(path):
            return path
    # Return last path as default if none of the previous ones matched
    return path


def get_tmuxinator_dir():
    """
    Return tmuxinator configuration directory.

    Checks for ``TMUXINATOR_CONFIG`` environmental variable.

    Returns
    -------
    str :
        absolute path to tmuxinator config directory

    See Also
    --------
    :meth:`tmuxp.config.import_tmuxinator`
    """
    if 'TMUXINATOR_CONFIG' in os.environ:
        return os.path.expanduser(os.environ['TMUXINATOR_CONFIG'])

    return os.path.expanduser('~/.tmuxinator/')


def get_teamocil_dir():
    """
    Return teamocil configuration directory.

    Returns
    -------
    str :
        absolute path to teamocil config directory

    See Also
    --------
    :meth:`tmuxp.config.import_teamocil`
    """
    return os.path.expanduser('~/.teamocil/')


def _validate_choices(options):
    """
    Callback wrapper for validating click.prompt input.

    Parameters
    ----------
    options : list
        List of allowed choices

    Returns
    -------
    :func:`callable`
        callback function for value_proc in :func:`click.prompt`.

    Raises
    ------
    :class:`click.BadParameter`
    """

    def func(value):
        if value not in options:
            raise click.BadParameter(
                'Possible choices are: {0}.'.format(', '.join(options))
            )
        return value

    return func


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
    cmd = ['set-hook', '-t', session.id, hook_name]
    hook_cmd = []
    attached_window = session.attached_window
    for window in session.windows:
        # unfortunately, select-layout won't work unless
        # we've literally selected the window at least once
        # with the client
        hook_cmd.append('selectw -t {}'.format(window.id))
        # edit: removed -t, or else it won't respect main-pane-w/h
        hook_cmd.append('selectl')
        hook_cmd.append('selectw -p')

    # unset the hook immediately after executing
    hook_cmd.append(
        'set-hook -u -t {target_session} {hook_name}'.format(
            target_session=session.id, hook_name=hook_name
        )
    )
    hook_cmd.append('selectw -t {}'.format(attached_window.id))

    # join the hook's commands with semicolons
    hook_cmd = '{}'.format('; '.join(hook_cmd))

    # append the hook command
    cmd.append(hook_cmd)

    # create the hook
    session.cmd(*cmd)


def is_pure_name(path):
    """
    Return True if path is a name and not a file path.

    Parameters
    ----------
    path : str
        Path (can be absolute, relative, etc.)

    Returns
    -------
    bool
        True if path is a name of config in config dir, not file path.
    """
    return (
        not os.path.isabs(path)
        and len(os.path.dirname(path)) == 0
        and not os.path.splitext(path)[1]
        and path != '.'
        and path != ''
    )


class ConfigPath(click.Path):
    def __init__(self, config_dir=None, *args, **kwargs):
        super(ConfigPath, self).__init__(*args, **kwargs)
        self.config_dir = config_dir

    def convert(self, value, param, ctx):
        config_dir = self.config_dir
        if callable(config_dir):
            config_dir = config_dir()

        value = scan_config(value, config_dir=config_dir)
        return super(ConfigPath, self).convert(value, param, ctx)


def scan_config_argument(ctx, param, value, config_dir=None):
    """Validate / translate config name/path values for click config arg.

    Wrapper on top of :func:`cli.scan_config`."""
    if callable(config_dir):
        config_dir = config_dir()

    if not config:
        tmuxp_echo("Enter at least one CONFIG")
        tmuxp_echo(ctx.get_help(), color=ctx.color)
        ctx.exit()

    if isinstance(value, string_types):
        value = scan_config(value, config_dir=config_dir)

    elif isinstance(value, tuple):
        value = tuple([scan_config(v, config_dir=config_dir) for v in value])

    return value


def get_abs_path(config):
    path = os.path
    join, isabs = path.join, path.isabs
    dirname, normpath = path.dirname, path.normpath
    cwd = os.getcwd()

    config = os.path.expanduser(config)
    if not isabs(config) or len(dirname(config)) > 1:
        config = normpath(join(cwd, config))

    return config


def _resolve_path_no_overwrite(config):
    path = get_abs_path(config)
    if os.path.exists(path):
        raise click.exceptions.UsageError('%s exists. Pick a new filename.' % path)
    return path


def scan_config(config, config_dir=None):
    """
    Return the real config path or raise an exception.

    If config is directory, scan for .tmuxp.{yaml,yml,json} in directory. If
    one or more found, it will warn and pick the first.

    If config is ".", "./" or None, it will scan current directory.

    If config is has no path and only a filename, e.g. "myconfig.yaml" it will
    search config dir.

    If config has no path and only a name with no extension, e.g. "myconfig",
    it will scan for file name with yaml, yml and json. If multiple exist, it
    will warn and pick the first.

    Parameters
    ----------
    config : str
        config file, valid examples:

        - a file name, myconfig.yaml
        - relative path, ../config.yaml or ../project
        - a period, .

    Raises
    ------
    :class:`click.exceptions.FileError`
    """
    if not config_dir:
        config_dir = get_config_dir()
    path = os.path
    exists, join, isabs = path.exists, path.join, path.isabs
    dirname, normpath, splitext = path.dirname, path.normpath, path.splitext
    cwd = os.getcwd()
    is_name = False
    file_error = None

    config = os.path.expanduser(config)
    # if purename, resolve to confg dir
    if is_pure_name(config):
        is_name = True
    elif (
        not isabs(config)
        or len(dirname(config)) > 1
        or config == '.'
        or config == ""
        or config == "./"
    ):  # if relative, fill in full path
        config = normpath(join(cwd, config))

    # no extension, scan
    if path.isdir(config) or not splitext(config)[1]:
        if is_name:
            candidates = [
                x
                for x in [
                    '%s%s' % (join(config_dir, config), ext)
                    for ext in VALID_CONFIG_DIR_FILE_EXTENSIONS
                ]
                if exists(x)
            ]
            if not len(candidates):
                file_error = (
                    'config not found in config dir (yaml/yml/json) %s '
                    'for name' % (config_dir)
                )
        else:
            candidates = [
                x
                for x in [
                    join(config, ext)
                    for ext in ['.tmuxp.yaml', '.tmuxp.yml', '.tmuxp.json']
                ]
                if exists(x)
            ]

            if len(candidates) > 1:
                tmuxp_echo(
                    click.style(
                        'Multiple .tmuxp.{yml,yaml,json} configs in %s'
                        % dirname(config),
                        fg="red",
                    )
                )
                tmuxp_echo(
                    click.wrap_text(
                        'This is undefined behavior, use only one. '
                        'Use file names e.g. myproject.json, coolproject.yaml. '
                        'You can load them by filename.'
                    )
                )
            elif not len(candidates):
                file_error = 'No tmuxp files found in directory'
        if len(candidates):
            config = candidates[0]
    elif not exists(config):
        file_error = 'file not found'

    if file_error:
        raise FileError(file_error, config)

    return config


def load_plugins(sconf):
    """
    Load and return plugins in config
    """
    plugins = []
    if 'plugins' in sconf:
        for plugin in sconf['plugins']:
            try:
                module_name = plugin.split('.')
                module_name = '.'.join(module_name[:-1])
                plugin_name = plugin.split('.')[-1]
                plugin = getattr(importlib.import_module(module_name), plugin_name)
                plugins.append(plugin())
            except exc.TmuxpPluginException as error:
                if not click.confirm(
                    '%sSkip loading %s?'
                    % (click.style(str(error), fg='yellow'), plugin_name),
                    default=True,
                ):
                    click.echo(
                        click.style('[Not Skipping] ', fg='yellow')
                        + 'Plugin versions constraint not met. Exiting...'
                    )
                    sys.exit(1)
            except Exception as error:
                click.echo(
                    click.style('[Plugin Error] ', fg='red')
                    + "Couldn\'t load {0}\n".format(plugin)
                    + click.style('{0}'.format(error), fg='yellow')
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
        proc = builder.session.cmd('display-message', '-p', "'#S'")
        for line in proc.stdout:
            print(line)

    if 'TMUX' in os.environ:
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

    if 'TMUX' in os.environ:  # tmuxp ran from inside tmux
        # unset TMUX, save it, e.g. '/tmp/tmux-1000/default,30668,0'
        tmux_env = os.environ.pop('TMUX')

        if has_gte_version('2.6'):
            set_layout_hook(builder.session, 'client-session-changed')

        builder.session.switch_client()  # switch client to new session

        os.environ['TMUX'] = tmux_env  # set TMUX back again
    else:
        if has_gte_version('2.6'):
            # if attaching for first time
            set_layout_hook(builder.session, 'client-attached')

            # for cases where user switches client for first time
            set_layout_hook(builder.session, 'client-session-changed')

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

    if has_gte_version('2.6'):  # prepare for both cases
        set_layout_hook(builder.session, 'client-attached')
        set_layout_hook(builder.session, 'client-session-changed')

    print('Session created in detached state.')


def _load_append_windows_to_current_session(builder):
    """
    Load config as new windows in current session

    Parameters
    ----------
    builder: :class:`workspacebuilder.WorkspaceBuilder`
    """
    current_attached_session = builder.find_current_attached_session()
    builder.build(current_attached_session, append=True)
    if has_gte_version('2.6'):  # prepare for both cases
        set_layout_hook(builder.session, 'client-attached')
        set_layout_hook(builder.session, 'client-session-changed')


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

    tmuxp will check and load a configuration file. The file will use kaptan
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
    config_file = os.path.realpath(config_file)

    tmuxp_echo(
        click.style('[Loading] ', fg='green')
        + click.style(config_file, fg='blue', bold=True)
    )

    # kaptan allows us to open a yaml or json file as a dict
    sconfig = kaptan.Kaptan()
    sconfig = sconfig.import_config(config_file).get()
    # shapes configurations relative to config / profile file location
    sconfig = config.expand(sconfig, os.path.dirname(config_file))
    # Overwrite session name
    if new_session_name:
        sconfig['session_name'] = new_session_name
    # propagate config inheritance (e.g. session -> window, window -> pane)
    sconfig = config.trickle(sconfig)

    t = Server(  # create tmux server object
        socket_name=socket_name, socket_path=socket_path,
        config_file=tmux_config_file, colors=colors,
    )

    which('tmux')  # raise exception if tmux not found

    try:  # load WorkspaceBuilder object for tmuxp config / tmux server
        builder = WorkspaceBuilder(
            sconf=sconfig, plugins=load_plugins(sconfig), server=t
        )
    except exc.EmptyConfigException:
        tmuxp_echo('%s is empty or parsed no config data' % config_file, err=True)
        return

    session_name = sconfig['session_name']

    # if the session already exists, prompt the user to attach
    if builder.session_exists(session_name) and not append:
        if not detached and (
            answer_yes
            or click.confirm(
                '%s is already running. Attach?'
                % click.style(session_name, fg='green'),
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
            if 'TMUX' in os.environ:  # tmuxp ran from inside tmux
                _load_append_windows_to_current_session(builder)
            else:
                _load_attached(builder, detached)

            return _setup_plugins(builder)

        # append and answer_yes have no meaning if specified together
        elif answer_yes:
            _load_attached(builder, detached)
            return _setup_plugins(builder)

        if 'TMUX' in os.environ:  # tmuxp ran from inside tmux
            msg = "Already inside TMUX, switch to session? yes/no\n"\
            "Or (a)ppend windows in the current active session?\n[y/n/a]"
            options = ['y', 'n', 'a']
            choice = click.prompt(msg, value_proc=_validate_choices(options))

            if choice == 'y':
                _load_attached(builder, detached)
            elif choice == 'a':
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
            'Error loading workspace. (k)ill, (a)ttach, (d)etach?',
            value_proc=_validate_choices(['k', 'a', 'd']),
            default='k',
        )

        if choice == 'k':
            builder.session.kill_session()
            tmuxp_echo('Session killed.')
        elif choice == 'a':
            _reattach(builder)
        else:
            sys.exit()

    return _setup_plugins(builder)



@click.group(context_settings={'obj': {}})
@click.version_option(__version__, '-V', '--version', message='%(prog)s %(version)s')
@click.option(
    '--log-level',
    default='INFO',
    help='Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)',
)
def cli(log_level):
    """Manage tmux sessions.

    Pass the "--help" argument to any command to see detailed help.
    See detailed documentation and examples at:
    http://tmuxp.git-pull.com/"""
    try:
        has_minimum_version()
    except TmuxCommandNotFound:
        tmuxp_echo('tmux not found. tmuxp requires you install tmux first.')
        sys.exit()
    except exc.TmuxpException as e:
        tmuxp_echo(e, err=True)
        sys.exit()
    setup_logger(logger=logger, level=log_level.upper())


def setup_logger(logger=None, level='INFO'):
    """
    Setup logging for CLI use.

    Tries to do some conditionals to prevent handlers from being added twice.
    Just to be safe.

    Parameters
    ----------
    logger : :py:class:`Logger`
        logger instance for tmuxp
    """
    if not logger:  # if no logger exists, make one
        logger = logging.getLogger()

    if not logger.handlers:  # setup logger handlers
        # channel = logging.StreamHandler()
        # channel.setFormatter(log.DebugLogFormatter())
        # channel.setFormatter(log.LogFormatter())

        logger.setLevel(level)
        # logger.addHandler(channel)


def startup(config_dir):
    """
    Initialize CLI.

    Parameters
    ----------
    str : get_config_dir(): Config directory to search
    """

    if not os.path.exists(config_dir):
        os.makedirs(config_dir)


@cli.command(name='shell')
@click.argument('session_name', nargs=1, required=False)
@click.argument('window_name', nargs=1, required=False)
@click.option('-S', 'socket_path', help='pass-through for tmux -S')
@click.option('-L', 'socket_name', help='pass-through for tmux -L')
@click.option(
    '-c',
    'command',
    help='Instead of opening shell, execute python code in libtmux and exit',
)
@click.option(
    '--best',
    'shell',
    flag_value='best',
    help='Use best shell available in site packages',
    default=True,
)
@click.option('--pdb', 'shell', flag_value='pdb', help='Use plain pdb')
@click.option(
    '--code', 'shell', flag_value='code', help='Use stdlib\'s code.interact()'
)
@click.option(
    '--ptipython', 'shell', flag_value='ptipython', help='Use ptpython + ipython'
)
@click.option('--ptpython', 'shell', flag_value='ptpython', help='Use ptpython')
@click.option('--ipython', 'shell', flag_value='ipython', help='Use ipython')
@click.option('--bpython', 'shell', flag_value='bpython', help='Use bpython')
@click.option(
    '--use-pythonrc/--no-startup',
    'use_pythonrc',
    help='Load PYTHONSTARTUP env var and ~/.pythonrc.py script in --code',
    default=False,
)
@click.option(
    '--use-vi-mode/--no-vi-mode',
    'use_vi_mode',
    help='Use vi-mode in ptpython/ptipython',
    default=False,
)
def command_shell(
    session_name,
    window_name,
    socket_name,
    socket_path,
    command,
    shell,
    use_pythonrc,
    use_vi_mode,
):
    """Launch python shell for tmux server, session, window and pane.

    Priority given to loaded session/wndow/pane objects:
    - session_name and window_name arguments
    - current shell: environmental variable of TMUX_PANE (which gives us window and
      session)
    - ``server.attached_session``, ``session.attached_window``, ``window.attached_pane``
    """
    server = Server(socket_name=socket_name, socket_path=socket_path)

    util.raise_if_tmux_not_running(server=server)

    current_pane = util.get_current_pane(server=server)

    session = util.get_session(
        server=server, session_name=session_name, current_pane=current_pane
    )

    window = util.get_window(
        session=session, window_name=window_name, current_pane=current_pane
    )

    pane = util.get_pane(window=window, current_pane=current_pane)  # NOQA: F841

    if command is not None:
        exec(command)
    else:
        if shell == 'pdb' or (os.getenv('PYTHONBREAKPOINT') and PY3 and PYMINOR >= 7):
            from ._compat import breakpoint as tmuxp_breakpoint

            tmuxp_breakpoint()
            return
        else:
            from .shell import launch

            launch(
                shell=shell,
                use_pythonrc=use_pythonrc,  # shell: code
                use_vi_mode=use_vi_mode,  # shell: ptpython, ptipython
                # tmux environment / libtmux variables
                server=server,
                session=session,
                window=window,
                pane=pane,
            )


@cli.command(name='freeze')
@click.argument('session_name', nargs=1, required=False)
@click.option('-S', 'socket_path', help='pass-through for tmux -S')
@click.option('-L', 'socket_name', help='pass-through for tmux -L')
@click.option('--force', 'force', help='overwrite the config file', is_flag=True)
def command_freeze(session_name, socket_name, socket_path, force):
    """Snapshot a session into a config.

    If SESSION_NAME is provided, snapshot that session. Otherwise, use the
    current session."""

    t = Server(socket_name=socket_name, socket_path=socket_path)

    try:
        if session_name:
            session = t.find_where({'session_name': session_name})
        else:
            session = t.list_sessions()[0]

        if not session:
            raise exc.TmuxpException('Session not found.')
    except exc.TmuxpException as e:
        print(e)
        return

    sconf = freeze(session)
    configparser = kaptan.Kaptan()
    newconfig = config.inline(sconf)
    configparser.import_config(newconfig)
    config_format = click.prompt(
        'Convert to', value_proc=_validate_choices(['yaml', 'json']), default='yaml'
    )

    if config_format == 'yaml':
        newconfig = configparser.export(
            'yaml', indent=2, default_flow_style=False, safe=True
        )
    elif config_format == 'json':
        newconfig = configparser.export('json', indent=2)
    else:
        sys.exit('Unknown config format.')

    print(
        '---------------------------------------------------------------'
        '\n'
        'Freeze does its best to snapshot live tmux sessions.\n'
    )
    if click.confirm(
        'The new config *WILL* require adjusting afterwards. Save config?'
    ):
        dest = None
        while not dest:
            save_to = os.path.abspath(
                os.path.join(
                    get_config_dir(),
                    '%s.%s' % (sconf.get('session_name'), config_format),
                )
            )
            dest_prompt = click.prompt(
                'Save to: %s' % save_to, value_proc=get_abs_path, default=save_to
            )
            if not force and os.path.exists(dest_prompt):
                print('%s exists. Pick a new filename.' % dest_prompt)
                continue

            dest = dest_prompt

        dest = os.path.abspath(os.path.relpath(os.path.expanduser(dest)))
        if click.confirm('Save to %s?' % dest):
            destdir = os.path.dirname(dest)
            if not os.path.isdir(destdir):
                os.makedirs(destdir)
            buf = open(dest, 'w')
            buf.write(newconfig)
            buf.close()

            print('Saved to %s.' % dest)
    else:
        print(
            'tmuxp has examples in JSON and YAML format at '
            '<http://tmuxp.git-pull.com/examples.html>\n'
            'View tmuxp docs at <http://tmuxp.git-pull.com/>.'
        )
        sys.exit()


@cli.command(name='load', short_help='Load tmuxp workspaces.')
@click.pass_context
@click.argument('config', type=ConfigPath(exists=True), nargs=-1)
@click.option('-S', 'socket_path', help='pass-through for tmux -S')
@click.option('-L', 'socket_name', help='pass-through for tmux -L')
@click.option('-f', 'tmux_config_file', help='pass-through for tmux -f')
@click.option('-s', 'new_session_name', help='start new session with new session name')
@click.option('--yes', '-y', 'answer_yes', help='yes', is_flag=True)
@click.option(
    '-d', 'detached', help='Load the session without attaching it', is_flag=True
)
@click.option(
    '-a',
    'append',
    help='Load configuration, appending windows to the current session',
    is_flag=True
)
@click.option(
    'colors',
    '-2',
    flag_value=256,
    default=True,
    help='Force tmux to assume the terminal supports 256 colours.',
)
@click.option(
    'colors',
    '-8',
    flag_value=88,
    help='Like -2, but indicates that the terminal supports 88 colours.',
)
@click.option('--log-file', help='File to log errors/output to')
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
        logger.addHandler(logfile_handler)

    tmux_options = {
        'socket_name': socket_name,
        'socket_path': socket_path,
        'tmux_config_file': tmux_config_file,
        'new_session_name': new_session_name,
        'answer_yes': answer_yes,
        'colors': colors,
        'detached': detached,
        'append': append,
    }

    if not config:
        tmuxp_echo("Enter at least one CONFIG")
        tmuxp_echo(ctx.get_help(), color=ctx.color)
        ctx.exit()

    if isinstance(config, string_types):
        load_workspace(config, **tmux_options)

    elif isinstance(config, tuple):
        config = list(config)
        # Load each configuration but the last to the background
        for cfg in config[:-1]:
            opt = tmux_options.copy()
            opt.update({'detached': True, 'new_session_name': None})
            load_workspace(cfg, **opt)

        # todo: obey the -d in the cli args only if user specifies
        load_workspace(config[-1], **tmux_options)


@cli.group(name='import')
def import_config_cmd():
    """Import a teamocil/tmuxinator config."""
    pass


def import_config(configfile, importfunc):
    configparser = kaptan.Kaptan(handler='yaml')

    configparser.import_config(configfile)
    newconfig = importfunc(configparser.get())
    configparser.import_config(newconfig)

    config_format = click.prompt(
        'Convert to', value_proc=_validate_choices(['yaml', 'json']), default='yaml'
    )

    if config_format == 'yaml':
        newconfig = configparser.export('yaml', indent=2, default_flow_style=False)
    elif config_format == 'json':
        newconfig = configparser.export('json', indent=2)
    else:
        sys.exit('Unknown config format.')

    tmuxp_echo(
        newconfig + '---------------------------------------------------------------'
        '\n'
        'Configuration import does its best to convert files.\n'
    )
    if click.confirm(
        'The new config *WILL* require adjusting afterwards. Save config?'
    ):
        dest = None
        while not dest:
            dest_path = click.prompt(
                'Save to [%s]' % os.getcwd(), value_proc=_resolve_path_no_overwrite
            )

            # dest = dest_prompt
            if click.confirm('Save to %s?' % dest_path):
                dest = dest_path

        buf = open(dest, 'w')
        buf.write(newconfig)
        buf.close()

        tmuxp_echo('Saved to %s.' % dest)
    else:
        tmuxp_echo(
            'tmuxp has examples in JSON and YAML format at '
            '<http://tmuxp.git-pull.com/examples.html>\n'
            'View tmuxp docs at <http://tmuxp.git-pull.com/>'
        )
        sys.exit()


@import_config_cmd.command(
    name='teamocil', short_help='Convert and import a teamocil config.'
)
@click.argument(
    'configfile', type=ConfigPath(exists=True, config_dir=get_teamocil_dir), nargs=1
)
def command_import_teamocil(configfile):
    """Convert a teamocil config from CONFIGFILE to tmuxp format and import
    it into tmuxp."""

    import_config(configfile, config.import_teamocil)


@import_config_cmd.command(
    name='tmuxinator', short_help='Convert and import a tmuxinator config.'
)
@click.argument(
    'configfile', type=ConfigPath(exists=True, config_dir=get_tmuxinator_dir), nargs=1
)
def command_import_tmuxinator(configfile):
    """Convert a tmuxinator config from CONFIGFILE to tmuxp format and import
    it into tmuxp."""
    import_config(configfile, config.import_tmuxinator)


@cli.command(name='convert')
@click.option(
    '--yes', '-y', 'confirmed', help='Auto confirms with "yes".', is_flag=True
)
@click.argument('config', type=ConfigPath(exists=True), nargs=1)
def command_convert(confirmed, config):
    """Convert a tmuxp config between JSON and YAML."""

    _, ext = os.path.splitext(config)
    if 'json' in ext:
        to_filetype = 'yaml'
    elif 'yaml' in ext:
        to_filetype = 'json'

    configparser = kaptan.Kaptan()
    configparser.import_config(config)
    newfile = config.replace(ext, '.%s' % to_filetype)

    export_kwargs = {'default_flow_style': False} if to_filetype == 'yaml' else {}
    newconfig = configparser.export(to_filetype, indent=2, **export_kwargs)

    if not confirmed:
        if click.confirm('convert to <%s> to %s?' % (config, to_filetype)):
            if click.confirm('Save config to %s?' % newfile):
                confirmed = True

    if confirmed:
        buf = open(newfile, 'w')
        buf.write(newconfig)
        buf.close()
        print('New config saved to <%s>.' % newfile)


@cli.command(
    name='ls', short_help='List configured sessions in {}.'.format(get_config_dir())
)
def command_ls():
    tmuxp_dir = get_config_dir()
    if os.path.exists(tmuxp_dir) and os.path.isdir(tmuxp_dir):
        for f in sorted(os.listdir(tmuxp_dir)):
            stem, ext = os.path.splitext(f)
            if os.path.isdir(f) or ext not in VALID_CONFIG_DIR_FILE_EXTENSIONS:
                continue
            print(stem)


@cli.command(name='debug-info', short_help='Print out all diagnostic info')
def command_debug_info():
    """
    Print debug info to submit with Issues.
    """

    def prepend_tab(strings):
        """
        Prepend tab to strings in list.
        """
        return list(map(lambda x: '\t%s' % x, strings))

    def output_break():
        """
        Generate output break.
        """
        return '-' * 25

    def format_tmux_resp(std_resp):
        """
        Format tmux command response for tmuxp stdout.
        """
        return '\n'.join(
            [
                '\n'.join(prepend_tab(std_resp.stdout)),
                click.style('\n'.join(prepend_tab(std_resp.stderr)), fg='red'),
            ]
        )

    output = [
        output_break(),
        'environment:\n%s'
        % '\n'.join(
            prepend_tab(
                [
                    'dist: %s' % platform.platform(),
                    'arch: %s' % platform.machine(),
                    'uname: %s' % '; '.join(platform.uname()[:3]),
                    'version: %s' % platform.version(),
                ]
            )
        ),
        output_break(),
        'python version: %s' % ' '.join(sys.version.split('\n')),
        'system PATH: %s' % os.environ['PATH'],
        'tmux version: %s' % get_version(),
        'libtmux version: %s' % libtmux_version,
        'tmuxp version: %s' % __version__,
        'tmux path: %s' % which('tmux'),
        'tmuxp path: %s' % tmuxp_path,
        'shell: %s' % os.environ['SHELL'],
        output_break(),
        'tmux sessions:\n%s' % format_tmux_resp(tmux_cmd('list-sessions')),
        'tmux windows:\n%s' % format_tmux_resp(tmux_cmd('list-windows')),
        'tmux panes:\n%s' % format_tmux_resp(tmux_cmd('list-panes')),
        'tmux global options:\n%s' % format_tmux_resp(tmux_cmd('show-options', '-g')),
        'tmux window options:\n%s'
        % format_tmux_resp(tmux_cmd('show-window-options', '-g')),
    ]

    tmuxp_echo('\n'.join(output))
