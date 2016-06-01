# -*- coding: utf-8 -*-
"""Command line tool for managing tmux workspaces and tmuxp configurations.

tmuxp.cli
~~~~~~~~~

"""
from __future__ import absolute_import, print_function, with_statement

import logging
import os
import sys

import click
import kaptan
from click.exceptions import FileError
from libtmux.common import has_required_tmux_version, which
from libtmux.server import Server

from . import WorkspaceBuilder, config, exc, log, util
from .__about__ import __version__
from ._compat import string_types
from .workspacebuilder import freeze

logger = logging.getLogger(__name__)


def config_dir():
    return os.path.expanduser('~/.tmuxp/')


def cwd_dir():
    return os.getcwd() + '/'
tmuxinator_config_dir = os.path.expanduser('~/.tmuxinator/')
teamocil_config_dir = os.path.expanduser('~/.teamocil/')


def _validate_choices(options):
    """Callback wrapper for validating click.prompt input.

    :param options: List of allowed choices
    :type options: list
    :rtype: func
    :returns: function for value_proc in :func:`click.prompt`.
    """

    def func(value):
        if value not in options:
            raise click.BadParameter(
                'Possible choices are: {0}.'.format(', '.join(options)))
        return value

    return func


def is_pure_name(path):
    """Return True if path is a name and not a file path."""
    return (
        not os.path.isabs(path) and
        len(os.path.dirname(path)) == 0 and
        not os.path.splitext(path)[1] and
        path != '.' and path != ''
    )


def resolve_config_argument(ctx, param, value):
    """Validate / translate config name/path values for click config arg.

    Wrapper on top of :func:`cli.resolve_config`."""
    if not config:
        click.echo("Enter at least one CONFIG")
        click.echo(ctx.get_help(), color=ctx.color)
        ctx.exit()

    if isinstance(value, string_types):
        value = resolve_config(value)

    elif isinstance(value, tuple):
        value = tuple(map(resolve_config, value))

    return value


def resolve_config(config):
    """Return the real config path or raise an exception.

    :param config: config file, valid examples:
        - a file name, myconfig.yaml
        - relative path, ../config.yaml or ../project
        - a period, .
    :type config: string

    If config is directory, scan for .tmuxp.{yaml,yml,json} in directory. If
    one or more found, it will warn and pick the first.

    If config is ".", "./" or None, it will scan current directory.

    If config is has no path and only a filename, e.g. "myconfig.yaml" it will
    search config dir.

    If config has no path and only a name with no extension, e.g. "myconfig",
    it will scan for file name with yaml, yml and json. If multiple exist, it
    will warn and pick the first.

    :raises: :class:`click.exceptions.FileError`
    """

    path = os.path
    exists, join, isabs = path.exists, path.join, path.isabs
    dirname, normpath, splitext = path.dirname, path.normpath, path.splitext
    cwd = os.getcwd()

    # is relative?    resolve to absolute via cwd
    # a is directory?   (scan dir for .tmuxp.{ext})
    # b no extension?   (scan config dir for .tmuxp.{ext})
    # c is absolute file?     continue
    # see if file exists, if not raise error

    config = os.path.expanduser(config)
    # if purename, resolve to confg dir
    if is_pure_name(config):
        config = join(config_dir(), config)
    elif (
        not isabs(config) or len(dirname(config)) > 1 or config == '.' or
        config == "" or config == "./"
    ):  # if relative, fill in full path
        config = normpath(join(cwd, config))

    # no extension, scan
    if not splitext(config)[1]:
        first = [join(config, ext)
                 for ext in ['.tmuxp.yaml', '.tmuxp.yml', '.tmuxp.json']]
        second = ['%s%s' % (config, ext) for ext in ['.yaml', '.yml', '.json']]
        candidates = [f for f in first + second if exists(f)]
        # print(candidates)
        # print([join(config, ext) for ext in first+second])
        if len(candidates) > 1:
            click.secho(
                'Multiple .tmuxp.{yml,yaml,json} configs in %s' %
                dirname(config), fg="red")
            click.echo(click.wrap_text(
                'This is undefined behavior, use only one. '
                'Additional projects may use a filename e.g. myproject.json, '
                'coolproject.yaml. You can load them by filename.'
            ))
        elif not len(candidates):
            raise FileError('No configs found', config)
        config = candidates[0]

    if not exists(config):
        raise FileError('File does not exist', config)

    return config


def load_workspace(
    config_file, socket_name=None, socket_path=None, colors=None,
    attached=None, detached=None, answer_yes=False
):
    """Build config workspace.

    :param config_file: full path to config file
    :param type: string

    """

    sconfig = kaptan.Kaptan()
    sconfig = sconfig.import_config(config_file).get()
    # expands configurations relative to config / profile file location
    sconfig = config.expand(sconfig, os.path.dirname(config_file))
    sconfig = config.trickle(sconfig)

    t = Server(
        socket_name=socket_name,
        socket_path=socket_path,
        colors=colors
    )

    try:
        builder = WorkspaceBuilder(sconf=sconfig, server=t)
    except exc.EmptyConfigException:
        click.echo('%s is empty or parsed no config data' %
                   config_file, err=True)
        return

    which('tmux')

    def reattach(session):
        if 'TMUX' in os.environ:
            session.switch_client()

        else:
            session.attach_session()

    session_name = sconfig['session_name']
    if builder.session_exists(session_name):
        if not detached and (
            answer_yes or click.confirm(
                '%s is already running. Attach?' %
                click.style(session_name, fg='green'), default=True)
        ):
            reattach(builder.session)
        return

    try:
        click.echo(
            click.style('[Loading] ', fg='green') +
            click.style(config_file, fg='blue', bold=True))
        builder.build()

        if 'TMUX' in os.environ:
            if not detached and (answer_yes or click.confirm(
                'Already inside TMUX, switch to session?'
            )):
                tmux_env = os.environ.pop('TMUX')
                builder.session.switch_client()

                os.environ['TMUX'] = tmux_env
                return builder.session
            else:
                sys.exit('Session created in detached state.')

        if not detached:
            builder.session.attach_session()
    except exc.TmuxpException as e:
        import traceback

        click.echo(traceback.format_exc(), err=True)
        click.echo(e, err=True)

        choice = click.prompt(
            'Error loading workspace. (k)ill, (a)ttach, (d)etach?',
            value_proc=_validate_choices(['k', 'a', 'd']),
            default='k'
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
@click.version_option(version=__version__, message='%(prog)s %(version)s')
@click.option('--log_level', default='INFO',
              help='Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
def cli(log_level):
    try:
        has_required_tmux_version()
    except exc.TmuxpException as e:
        click.echo(e, err=True)
        sys.exit()
    setup_logger(
        level=log_level.upper()
    )


def setup_logger(logger=None, level='INFO'):
    """Setup logging for CLI use.

    :param logger: instance of logger
    :type logger: :py:class:`Logger`

    """
    if not logger:
        logger = logging.getLogger()
    if not logger.handlers:
        channel = logging.StreamHandler()
        channel.setFormatter(log.DebugLogFormatter())

        # channel.setFormatter(log.LogFormatter())
        logger.setLevel(level)
        logger.addHandler(channel)


def startup(config_dir):
    """Initialize CLI.

    :param config_dir(): Config directory to search
    :type config_dir(): string

    """

    if not os.path.exists(config_dir):
        os.makedirs(config_dir)


@cli.command(name='freeze')
@click.argument('session_name', nargs=1)
@click.option('-S', 'socket_path', help='pass-through for tmux -L')
@click.option('-L', 'socket_name', help='pass-through for tmux -L')
def command_freeze(session_name, socket_name, socket_path):
    """Import teamocil config to tmuxp format."""

    t = Server(
        socket_name=socket_name,
        socket_path=socket_path,
    )

    try:
        session = t.find_where({
            'session_name': session_name
        })

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
        'Convert to',
        value_proc=_validate_choices(['yaml', 'json']),
        default='yaml'
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
        'Configuration import does its best to convert teamocil files.\n'
    )
    if click.confirm(
        'The new config *WILL* require adjusting afterwards. Save config?'
    ):
        dest = None
        while not dest:
            save_to = os.path.abspath(
                os.path.join(
                    config_dir(),
                    '%s.%s' % (sconf.get('session_name'), config_format)
                )
            )
            dest_prompt = click.prompt('Save to: ', save_to)
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


@cli.command(name='load')
@click.pass_context
@click.argument('config', click.Path(exists=True), nargs=-1,
                callback=resolve_config_argument)
@click.option('-S', 'socket_path', help='pass-through for tmux -L')
@click.option('-L', 'socket_name', help='pass-through for tmux -L')
@click.option('--yes', '-y', 'answer_yes', help='yes', is_flag=True)
@click.option('-d', 'detached',
              help='Load the session without attaching it', is_flag=True)
@click.option(
    '-2', 'colors', flag_value=256, default=True,
    help='Force tmux to assume the terminal supports 256 colours.')
@click.option(
    '-8', 'colors', flag_value=88,
    help='Like -2, but indicates that the terminal supports 88 colours.')
def command_load(ctx, config, socket_name, socket_path, answer_yes,
                 detached, colors):
    """Load a tmux workspace from one or multiple CONFIG path to config file,
    directory with config file or session name.
    """
    util.oh_my_zsh_auto_title()

    tmux_options = {
        'socket_name': socket_name,
        'socket_path': socket_path,
        'answer_yes': answer_yes,
        'colors': colors,
        'detached': detached
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
            # todo: add -d option to all these
            load_workspace(cfg, **tmux_options)

        # todo: obey the -d in the cli args only if user specifies
        load_workspace(config[-1], **tmux_options)


@cli.group(name='import')
def import_config():
    pass


@import_config.command(name='teamocil')
@click.argument('configfile', click.Path(exists=True), nargs=1)
@click.option('--list', '-l', 'list_configs', help='yes', is_flag=True)
def command_import_teamocil(configfile, list_configs):
    """Import teamocil config to tmuxp format."""

    if list_configs:
        try:
            configs_in_user = config.in_dir(
                teamocil_config_dir(), extensions='yml')
        except OSError:
            configs_in_user = []
        configs_in_cwd = config.in_dir(
            config_dir=cwd_dir(), extensions='yml')

        output = ''

        if not os.path.exists(teamocil_config_dir):
            output += '# %s: \n\tDirectory doesn\'t exist.\n' % \
                teamocil_config_dir()
        elif not configs_in_user:
            output += '# %s: \n\tNone found.\n' % teamocil_config_dir()
        else:
            output += '# %s: \n\t%s\n' % (
                config_dir(), ', '.join(configs_in_user)
            )

        if configs_in_cwd:
            output += '# current directory:\n\t%s' % (
                ', '.join(configs_in_cwd)
            )

        print(output)
    elif configfile:
        configfile = os.path.abspath(os.path.relpath(
            os.path.expanduser(configfile)))
        configparser = kaptan.Kaptan(handler='yaml')

        if os.path.exists(configfile):
            print(configfile)
            configparser.import_config(configfile)
            newconfig = config.import_teamocil(configparser.get())
            configparser.import_config(newconfig)
        else:
            sys.exit('File not found: %s' % configfile)

        config_format = click.prompt(
            'Convert to',
            value_proc=_validate_choices(['yaml', 'json']),
            default='yaml'
        )

        if config_format == 'yaml':
            newconfig = configparser.export(
                'yaml', indent=2, default_flow_style=False
            )
        elif config_format == 'json':
            newconfig = configparser.export('json', indent=2)
        else:
            sys.exit('Unknown config format.')

        print(newconfig)
        print(
            '---------------------------------------------------------------'
            '\n'
            'Configuration import does its best to convert teamocil files.\n'
        )
        if click.confirm(
            'The new config *WILL* require adjusting afterwards. Save config?'
        ):
            dest = None
            while not dest:
                dest_prompt = click.prompt('Save to: %s ' % os.path.abspath(
                    os.path.join(config_dir(), 'myimport.%s' % config_format)))
                if os.path.exists(dest_prompt):
                    print('%s exists. Pick a new filename.' % dest_prompt)
                    continue

                dest = dest_prompt

            dest = os.path.abspath(os.path.relpath(os.path.expanduser(dest)))
            if click.confirm('Save to %s?' % dest):
                buf = open(dest, 'w')
                buf.write(newconfig)
                buf.close()

                print('Saved to %s.' % dest)
        else:
            print(
                'tmuxp has examples in JSON and YAML format at '
                '<http://tmuxp.readthedocs.io/en/latest/examples.html>\n'
                'View tmuxp docs at <http://tmuxp.readthedocs.io/>'
            )
            sys.exit()


@import_config.command(name='tmuxinator')
@click.argument('configfile', click.Path(exists=True), nargs=1)
@click.option('--list', '-l', 'list_configs', help='yes', is_flag=True)
def command_import_tmuxinator(configfile, list_configs):
    """Import tmuxinator config to tmuxp format."""
    if list_configs:
        try:
            configs_in_user = config.in_dir(
                tmuxinator_config_dir(), extensions='yml')
        except OSError:
            configs_in_user = []
        configs_in_cwd = config.in_dir(
            config_dir=cwd_dir(), extensions='yml')

        output = ''

        if not os.path.exists(tmuxinator_config_dir()):
            output += '# %s: \n\tDirectory doesn\'t exist.\n' % \
                tmuxinator_config_dir()
        elif not configs_in_user:
            output += '# %s: \n\tNone found.\n' % tmuxinator_config_dir()
        else:
            output += '# %s: \n\t%s\n' % (
                config_dir(), ', '.join(configs_in_user)
            )

        if configs_in_cwd:
            output += '# current directory:\n\t%s' % (
                ', '.join(configs_in_cwd)
            )

        print(output)
    elif configfile:
        configfile = os.path.abspath(os.path.relpath(
            os.path.expanduser(configfile)))
        configparser = kaptan.Kaptan(handler='yaml')

        if os.path.exists(configfile):
            print(configfile)
            configparser.import_config(configfile)
            newconfig = config.import_tmuxinator(configparser.get())
            configparser.import_config(newconfig)
        else:
            sys.exit('File not found: %s' % configfile)

        config_format = click.prompt(
            'Convert to',
            value_proc=_validate_choices(['yaml', 'json']),
            default='yaml'
        )

        if config_format == 'yaml':
            newconfig = configparser.export(
                'yaml', indent=2, default_flow_style=False
            )
        elif config_format == 'json':
            newconfig = configparser.export('json', indent=2)
        else:
            sys.exit('Unknown config format.')

        print(newconfig)
        print(
            '---------------------------------------------------------------'
            '\n'
            'Configuration import does its best to convert tmuxinator files.'
            '\n'
        )
        if click.confirm(
            'The new config *WILL* require adjusting afterwards. Save config?'
        ):
            dest = None
            while not dest:
                dest_prompt = click.prompt('Save to: %s' % os.path.abspath(
                    os.path.join(config_dir(), 'myimport.%s' % config_format)))
                if os.path.exists(dest_prompt):
                    print('%s exists. Pick a new filename.' % dest_prompt)
                    continue

                dest = dest_prompt

            dest = os.path.abspath(os.path.relpath(os.path.expanduser(dest)))
            if click.confirm('Save to %s?' % dest):
                buf = open(dest, 'w')
                buf.write(newconfig)
                buf.close()

                print('Saved to %s.' % dest)
        else:
            print(
                'tmuxp has examples in JSON and YAML format at '
                '<http://tmuxp.readthedocs.io/en/latest/examples.html>\n'
                'View tmuxp docs at <http://tmuxp.readthedocs.io/>'
            )
            sys.exit()


@cli.command(name='convert')
@click.argument('config', click.Path(exists=True), nargs=1,
                callback=resolve_config_argument)
def command_convert(config):
    """Convert tmuxp config to and from JSON and YAML."""

    _, ext = os.path.splitext(config)
    if 'json' in ext:
        if click.confirm(
            'convert to <%s> to yaml?' % config
        ):
            configparser = kaptan.Kaptan()
            configparser.import_config(config)
            newfile = config.replace(ext, '.yaml')
            newconfig = configparser.export(
                'yaml', indent=2, default_flow_style=False
            )
            if click.confirm(
                'Save config to %s?' % newfile
            ):
                buf = open(newfile, 'w')
                buf.write(newconfig)
                buf.close()
                print('New config saved to %s' % newfile)
    elif 'yaml' in ext:
        if click.confirm(
            'convert to <%s> to json?' % config
        ):
            configparser = kaptan.Kaptan()
            configparser.import_config(config)
            newfile = config.replace(ext, '.json')
            newconfig = configparser.export('json', indent=2)
            print(newconfig)
            if click.confirm(
                'Save config to <%s>?' % newfile
            ):
                buf = open(newfile, 'w')
                buf.write(newconfig)
                buf.close()
                print('New config saved to <%s>.' % newfile)
