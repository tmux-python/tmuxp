# -*- coding: utf-8 -*-
"""Command line tool for managing tmux workspaces and tmuxp configurations.

tmuxp.cli
~~~~~~~~~

"""
from __future__ import absolute_import

import logging
import os
import sys

import click
import kaptan
from click.exceptions import FileError

from libtmux.common import has_gte_version, has_minimum_version, which
from libtmux.exc import TmuxCommandNotFound
from libtmux.server import Server

from . import config, exc, log, util
from .__about__ import __version__
from ._compat import string_types
from .workspacebuilder import WorkspaceBuilder, freeze

logger = logging.getLogger(__name__)


def get_cwd():
    return os.getcwd()


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
    for window in session.windows:
        # unfortunately, select-layout won't work unless
        # we've literally selected the window at least once
        # with the client
        hook_cmd.append('selectw -t {}'.format(window.id))
        # edit: removed -t, or else it won't respect main-pane-w/h
        hook_cmd.append('selectl'.format(window.id))
        hook_cmd.append('selectw -p'.format(window.id))

    # unset the hook immediately after executing
    hook_cmd.append(
        'set-hook -u -t {target_session} {hook_name}'.format(
            target_session=session.id, hook_name=hook_name
        )
    )

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
        click.echo("Enter at least one CONFIG")
        click.echo(ctx.get_help(), color=ctx.color)
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
    if not splitext(config)[1]:
        if is_name:
            candidates = [
                x
                for x in [
                    '%s%s' % (join(config_dir, config), ext)
                    for ext in ['.yaml', '.yml', '.json']
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
                click.secho(
                    'Multiple .tmuxp.{yml,yaml,json} configs in %s' % dirname(config),
                    fg="red",
                )
                click.echo(
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


def _reattach(session):
    """
    Reattach session (depending on env being inside tmux already or not)

    Parameters
    ----------
    session : :class:`libtmux.Session`

    Notes
    -----
    If ``TMUX`` environmental variable exists in the environment this script is
    running, that means we're in a tmux client. So ``tmux switch-client`` will
    load the session.

    If not, ``tmux attach-session`` loads the client to the target session.
    """
    if 'TMUX' in os.environ:
        session.switch_client()

    else:
        session.attach_session()


def load_workspace(
    config_file,
    socket_name=None,
    socket_path=None,
    colors=None,
    detached=False,
    answer_yes=False,
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
    colors : str, optional
        '-2'
            Force tmux to support 256 colors
    detached : bool
        Force detached state. default False.
    answer_yes : bool
        Assume yes when given prompt. default False.

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

    # kaptan allows us to open a yaml or json file as a dict
    sconfig = kaptan.Kaptan()
    sconfig = sconfig.import_config(config_file).get()
    # shapes configurations relative to config / profile file location
    sconfig = config.expand(sconfig, os.path.dirname(config_file))
    # propagate config inheritance (e.g. session -> window, window -> pane)
    sconfig = config.trickle(sconfig)

    t = Server(  # create tmux server object
        socket_name=socket_name, socket_path=socket_path, colors=colors
    )

    which('tmux')  # raise exception if tmux not found

    try:  # load WorkspaceBuilder object for tmuxp config / tmux server
        builder = WorkspaceBuilder(sconf=sconfig, server=t)
    except exc.EmptyConfigException:
        click.echo('%s is empty or parsed no config data' % config_file, err=True)
        return

    session_name = sconfig['session_name']

    # if the session already exists, prompt the user to attach. tmuxp doesn't
    # support incremental session building or appending (yet, PR's welcome!)
    if builder.session_exists(session_name):
        if not detached and (
            answer_yes
            or click.confirm(
                '%s is already running. Attach?'
                % click.style(session_name, fg='green'),
                default=True,
            )
        ):
            _reattach(builder.session)
        return

    try:
        click.echo(
            click.style('[Loading] ', fg='green')
            + click.style(config_file, fg='blue', bold=True)
        )

        builder.build()  # load tmux session via workspace builder

        if 'TMUX' in os.environ:  # tmuxp ran from inside tmux
            if not detached and (
                answer_yes or click.confirm('Already inside TMUX, switch to session?')
            ):
                # unset TMUX, save it, e.g. '/tmp/tmux-1000/default,30668,0'
                tmux_env = os.environ.pop('TMUX')

                if has_gte_version('2.6'):
                    set_layout_hook(builder.session, 'client-session-changed')

                builder.session.switch_client()  # switch client to new session

                os.environ['TMUX'] = tmux_env  # set TMUX back again
                return builder.session
            else:  # session created in the background, from within tmux
                if has_gte_version('2.6'):  # prepare for both cases
                    set_layout_hook(builder.session, 'client-attached')
                    set_layout_hook(builder.session, 'client-session-changed')

                sys.exit('Session created in detached state.')
        else:  # tmuxp ran from inside tmux
            if has_gte_version('2.6'):
                # if attaching for first time
                set_layout_hook(builder.session, 'client-attached')

                # for cases where user switches client for first time
                set_layout_hook(builder.session, 'client-session-changed')

            if not detached:
                builder.session.attach_session()

    except exc.TmuxpException as e:
        import traceback

        click.echo(traceback.format_exc(), err=True)
        click.echo(e, err=True)

        choice = click.prompt(
            'Error loading workspace. (k)ill, (a)ttach, (d)etach?',
            value_proc=_validate_choices(['k', 'a', 'd']),
            default='k',
        )

        if choice == 'k':
            builder.session.kill_session()
            click.echo('Session killed.')
        elif choice == 'a':
            if 'TMUX' in os.environ:
                builder.session.switch_client()
            else:
                builder.session.attach_session()
        else:
            sys.exit()

    return builder.session


@click.group(context_settings={'obj': {}})
@click.version_option(__version__, '-V', '--version', message='%(prog)s %(version)s')
@click.option(
    '--log_level',
    default='INFO',
    help='Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)',
)
def cli(log_level):
    """Manage tmux sessions.

    Pass the "--help" argument to any command to see detailed help.
    See detailed documentation and examples at:
    http://tmuxp.readthedocs.io/en/latest/"""
    try:
        has_minimum_version()
    except TmuxCommandNotFound:
        click.echo('tmux not found. tmuxp requires you install tmux first.')
        sys.exit()
    except exc.TmuxpException as e:
        click.echo(e, err=True)
        sys.exit()
    setup_logger(level=log_level.upper())


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
        channel = logging.StreamHandler()
        channel.setFormatter(log.DebugLogFormatter())

        # channel.setFormatter(log.LogFormatter())
        logger.setLevel(level)
        logger.addHandler(channel)


def startup(config_dir):
    """
    Initialize CLI.

    Parameters
    ----------
    str : get_config_dir(): Config directory to search
    """

    if not os.path.exists(config_dir):
        os.makedirs(config_dir)


@cli.command(name='freeze')
@click.argument('session_name', nargs=1, required=False)
@click.option('-S', 'socket_path', help='pass-through for tmux -S')
@click.option('-L', 'socket_name', help='pass-through for tmux -L')
def command_freeze(session_name, socket_name, socket_path):
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

    print(newconfig)
    print(
        '---------------------------------------------------------------'
        '\n'
        'Freeze does it best to snapshot live tmux sessions.\n'
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
            if os.path.exists(dest_prompt):
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
            '<http://tmuxp.readthedocs.io/en/latest/examples.html>\n'
            'View tmuxp docs at <http://tmuxp.readthedocs.io/>.'
        )
        sys.exit()


@cli.command(name='load', short_help='Load tmuxp workspaces.')
@click.pass_context
@click.argument('config', type=ConfigPath(exists=True), nargs=-1)
@click.option('-S', 'socket_path', help='pass-through for tmux -S')
@click.option('-L', 'socket_name', help='pass-through for tmux -L')
@click.option('--yes', '-y', 'answer_yes', help='yes', is_flag=True)
@click.option(
    '-d', 'detached', help='Load the session without attaching it', is_flag=True
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
def command_load(ctx, config, socket_name, socket_path, answer_yes, detached, colors):
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

    tmux_options = {
        'socket_name': socket_name,
        'socket_path': socket_path,
        'answer_yes': answer_yes,
        'colors': colors,
        'detached': detached,
    }

    if not config:
        click.echo("Enter at least one CONFIG")
        click.echo(ctx.get_help(), color=ctx.color)
        ctx.exit()

    if isinstance(config, string_types):
        load_workspace(config, **tmux_options)

    elif isinstance(config, tuple):
        config = list(config)
        # Load each configuration but the last to the background
        for cfg in config[:-1]:
            opt = tmux_options.copy()
            opt.update({'detached': True})
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

    click.echo(
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

        click.echo('Saved to %s.' % dest)
    else:
        click.echo(
            'tmuxp has examples in JSON and YAML format at '
            '<http://tmuxp.readthedocs.io/en/latest/examples.html>\n'
            'View tmuxp docs at <http://tmuxp.readthedocs.io/>'
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
@click.argument('config', type=ConfigPath(exists=True), nargs=1)
def command_convert(config):
    """Convert a tmuxp config between JSON and YAML."""

    _, ext = os.path.splitext(config)
    if 'json' in ext:
        if click.confirm('convert to <%s> to yaml?' % config):
            configparser = kaptan.Kaptan()
            configparser.import_config(config)
            newfile = config.replace(ext, '.yaml')
            newconfig = configparser.export('yaml', indent=2, default_flow_style=False)
            if click.confirm('Save config to %s?' % newfile):
                buf = open(newfile, 'w')
                buf.write(newconfig)
                buf.close()
                print('New config saved to %s' % newfile)
    elif 'yaml' in ext:
        if click.confirm('convert to <%s> to json?' % config):
            configparser = kaptan.Kaptan()
            configparser.import_config(config)
            newfile = config.replace(ext, '.json')
            newconfig = configparser.export('json', indent=2)
            print(newconfig)
            if click.confirm('Save config to <%s>?' % newfile):
                buf = open(newfile, 'w')
                buf.write(newconfig)
                buf.close()
                print('New config saved to <%s>.' % newfile)
