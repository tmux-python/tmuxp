# -*- coding: utf8 - *-
"""Command line tool for managing tmux workspaces and tmuxp configurations.

tmuxp.cli
~~~~~~~~~

:copyright: Copyright 2013 Tony Narlock.
:license: BSD, see LICENSE for details

"""

import os
import sys
import argparse
import argcomplete
import logging
import kaptan
from . import log, util, exc, WorkspaceBuilder, Server, config
from .util import ascii_lowercase, input
from .workspacebuilder import freeze
from distutils.util import strtobool


import re
VERSIONFILE = os.path.join(os.path.abspath(os.path.dirname(__file__)), '__init__.py')
verstrline = open(VERSIONFILE, "rt").read()
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VSRE, verstrline, re.M)
if mo:
    __version__ = mo.group(1)
#import pkg_resources
#__version__ = pkg_resources.require("tmuxp")[0].version

logger = logging.getLogger(__name__)

config_dir = os.path.expanduser('~/.tmuxp/')
cwd_dir = os.getcwd() + '/'
tmuxinator_config_dir = os.path.expanduser('~/.tmuxinator/')
teamocil_config_dir = os.path.expanduser('~/.teamocil/')


def prompt(name, default=None):
    """Return user input from command line.

    :meth:`~prompt`, :meth:`~prompt_bool` and :meth:`prompt_choices` are from
    `flask-script`_. See the `flask-script license`_.

    .. _flask-script: https://github.com/techniq/flask-script
    .. _flask-script license:
        https://github.com/techniq/flask-script/blob/master/LICENSE

    :param name: prompt text
    :param default: default value if no input provided.
    :rtype: string

    """

    prompt = name + (default and ' [%s]' % default or '')
    prompt += name.endswith('?') and ' ' or ': '
    while True:
        rv = input(prompt)
        if rv:
            return rv
        if default is not None:
            return default


def prompt_bool(name, default=False, yes_choices=None, no_choices=None):
    """Return user input from command line and converts to boolean value.

    :param name: prompt text
    :param default: default value if no input provided.
    :param yes_choices: default 'y', 'yes', '1', 'on', 'true', 't'
    :param no_choices: default 'n', 'no', '0', 'off', 'false', 'f'
    :rtype: bool

    """

    yes_choices = yes_choices or ('y', 'yes', '1', 'on', 'true', 't')
    no_choices = no_choices or ('n', 'no', '0', 'off', 'false', 'f')

    if default is None:
        prompt_choice = 'y/n'
    elif default is True:
        prompt_choice = 'Y/n'
    else:
        prompt_choice = 'y/N'

    prompt = name + ' [%s]' % prompt_choice
    prompt += name.endswith('?') and ' ' or ': '

    while True:
        rv = input(prompt)
        if not rv:
            return default
        if rv.lower() in yes_choices:
            return True
        elif rv.lower() in no_choices:
            return False


def prompt_yes_no(name, default=True):
    """:meth:`prompt_bool()` returning yes by default."""
    return prompt_bool(name, default=default)


def prompt_choices(name, choices, default=None, resolve=ascii_lowercase,
                   no_choice=('none',)):
    """Return user input from command line from set of provided choices.

    :param name: prompt text
    :param choices: list or tuple of available choices. Choices may be
                    single strings or (key, value) tuples.
    :param default: default value if no input provided.
    :param no_choice: acceptable list of strings for "null choice"
    :rtype: str

    """

    _choices = []
    options = []

    for choice in choices:
        if isinstance(choice, basestring):
            options.append(choice)
        else:
            options.append("%s [%s]" % (choice[1], choice[0]))
            choice = choice[0]
        _choices.append(choice)

    while True:
        rv = prompt(name + ' - (%s)' % ', '.join(options), default)
        if not rv:
            return default
        rv = resolve(rv)
        if rv in no_choice:
            return None
        if rv in _choices:
            return rv


class ConfigFileCompleter(argcomplete.completers.FilesCompleter):

    """argcomplete completer for tmuxp files."""

    def __call__(self, prefix, **kwargs):

        completion = argcomplete.completers.FilesCompleter.__call__(
            self, prefix, **kwargs
        )

        completion += [os.path.join(config_dir, c)
                       for c in config.in_dir(config_dir)]

        return completion


class TmuxinatorCompleter(argcomplete.completers.FilesCompleter):

    """argcomplete completer for Tmuxinator files."""

    def __call__(self, prefix, **kwargs):
        completion = argcomplete.completers.FilesCompleter.__call__(
            self, prefix, **kwargs
        )

        tmuxinator_configs = config.in_dir(
            tmuxinator_config_dir, extensions='yml'
        )
        completion += [
            os.path.join(tmuxinator_config_dir, f)
            for f in tmuxinator_configs
        ]

        return completion


class TeamocilCompleter(argcomplete.completers.FilesCompleter):

    """argcomplete completer for Teamocil files."""

    def __call__(self, prefix, **kwargs):
        completion = argcomplete.completers.FilesCompleter.__call__(
            self, prefix, **kwargs
        )

        teamocil_configs = config.in_dir(teamocil_config_dir, extensions='yml')
        completion += [
            os.path.join(teamocil_config_dir, f)
            for f in teamocil_configs
        ]

        return completion


def SessionCompleter(prefix, parsed_args, **kwargs):
    """Return list of session names for argcomplete completer."""

    t = Server(
        socket_name=parsed_args.socket_name,
        socket_path=parsed_args.socket_path
    )

    sessions_available = [
        s.get('session_name') for s in t._sessions
        if s.get('session_name').startswith(' '.join(prefix))
    ]

    if parsed_args.session_name and sessions_available:
        return []

    return [
        s.get('session_name') for s in t._sessions
        if s.get('session_name').startswith(prefix)
    ]


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

    :param config_dir: Config directory to search
    :type config_dir: string

    """

    if not os.path.exists(config_dir):
        os.makedirs(config_dir)


def load_workspace(config_file, args):
    """Build config workspace.

    :param config_file: full path to config file
    :param type: string

    """
    logger.info('Loading %s.' % config_file)

    sconfig = kaptan.Kaptan()
    sconfig = sconfig.import_config(config_file).get()
    sconfig = config.expand(sconfig, os.path.dirname(config_file))
    sconfig = config.trickle(sconfig)

    t = Server(
        socket_name=args.socket_name,
        socket_path=args.socket_path,
        colors=args.colors
    )

    try:
        builder = WorkspaceBuilder(sconf=sconfig, server=t)
    except exc.EmptyConfigException:
        logger.error('%s is empty or parsed no config data' % config_file)
        return

    tmux_bin = util.which('tmux')

    try:
        builder.build()

        if 'TMUX' in os.environ:
            if args.answer_yes or prompt_yes_no('Already inside TMUX, switch to session?'):
                tmux_env = os.environ.pop('TMUX')
                builder.session.switch_client()

                os.environ['TMUX'] = tmux_env
                return
            else:
                sys.exit('Session created in detached state.')

        builder.session.attach_session()
    except exc.TmuxSessionExists as e:
        if args.answer_yes or prompt_yes_no('%s Attach?' % e):
            if 'TMUX' in os.environ:
                builder.session.switch_client()

            else:
                builder.session.attach_session()
        return
    except exc.TmuxpException as e:
        import traceback

        print(traceback.format_exc())
        logger.error(e)

        choice = prompt_choices(
            'Error loading workspace. (k)ill, (a)ttach, (d)etach?',
            choices=['k', 'a', 'd'],
            default='k'
        )

        if choice == 'k':
            builder.session.kill_session()
            print('Session killed.')
        elif choice == 'a':
            if 'TMUX' in os.environ:
                builder.session.switch_client()
            else:
                builder.session.attach_session()
        else:
            sys.exit()


def command_freeze(args):
    """Import teamocil config to tmuxp format."""

    ctext = ' '.join(args.session_name)

    t = Server(
        socket_name=args.socket_name,
        socket_path=args.socket_path,
        colors=args.colors
    )

    session = t.findWhere({
        'session_name': ctext
    })

    sconf = freeze(session)
    configparser = kaptan.Kaptan()
    newconfig = config.inline(sconf)
    configparser.import_config(newconfig)
    config_format = prompt_choices('Convert to', choices=[
        'yaml', 'json'], default='yaml')

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
        '---------------------------------------------------------------')
    print(
        'Configuration import does its best to convert teamocil files.\n')
    if args.answer_yes or prompt_yes_no(
        'The new config *WILL* require adjusting afterwards. Save config?'
    ):
        dest = None
        while not dest:
            dest_prompt = prompt('Save to: ', os.path.abspath(
                os.path.join(config_dir, '%s.%s' % (sconf.get('session_name'), config_format))))
            if os.path.exists(dest_prompt):
                print('%s exists. Pick a new filename.' % dest_prompt)
                continue

            dest = dest_prompt

        dest = os.path.abspath(os.path.relpath(os.path.expanduser(dest)))
        if args.answer_yes or prompt_yes_no('Write to %s?' % dest):
            buf = open(dest, 'w')
            buf.write(newconfig)
            buf.close()

            print('Saved to %s.' % dest)
    else:
        print(
            'tmuxp has examples in JSON and YAML format at <http://tmuxp.readthedocs.org/en/latest/examples.html>\n'
            'View tmuxp docs at <http://tmuxp.readthedocs.org/>'
        )
        sys.exit()


def command_load(args):
    """Load a session from a tmuxp session file."""
    if args.list:
        startup(config_dir)
        configs_in_user = config.in_dir(config_dir)
        configs_in_cwd = config.in_cwd()

        sys.exit()

        output = ''

        if not configs_in_user:
            output += '# %s: \n\tNone found.\n' % config_dir
        else:
            output += '# %s: \n\t%s\n' % (
                config_dir, ', '.join(configs_in_user)
            )

        if configs_in_cwd:
            output += '# current directory:\n\t%s' % (
                ', '.join(configs_in_cwd)
            )

        print(output)
        return

    elif args.config:
        if '.' == args.config:
            if config.in_cwd():
                configfile = config.in_cwd()[0]
                print(configfile)
            else:
                sys.exit('No tmuxp configs found in current directory.')
        else:
            configfile = args.config
        file_user = os.path.join(config_dir, configfile)
        file_cwd = os.path.join(cwd_dir, configfile)

        if os.path.exists(file_cwd) and os.path.isfile(file_cwd):
            print('load %s' % file_cwd)
            load_workspace(file_cwd, args)
        elif os.path.exists(file_user) and os.path.isfile(file_user):
            load_workspace(file_user, args)
        else:
            logger.error('%s not found.' % configfile)


def command_import_teamocil(args):
    """Import teamocil config to tmuxp format."""

    if args.list:
        try:
            configs_in_user = config.in_dir(
                teamocil_config_dir, extensions='yml')
        except OSError:
            configs_in_user = []
        configs_in_cwd = config.in_dir(
            config_dir=cwd_dir, extensions='yml')

        output = ''

        if not os.path.exists(teamocil_config_dir):
            output += '# %s: \n\tDirectory doesn\'t exist.\n' % teamocil_config_dir
        elif not configs_in_user:
            output += '# %s: \n\tNone found.\n' % teamocil_config_dir
        else:
            output += '# %s: \n\t%s\n' % (
                config_dir, ', '.join(configs_in_user)
            )

        if configs_in_cwd:
            output += '# current directory:\n\t%s' % (
                ', '.join(configs_in_cwd)
            )

        print(output)
    elif args.config:
        configfile = os.path.abspath(os.path.relpath(
            os.path.expanduser(args.config)))
        configparser = kaptan.Kaptan(handler='yaml')

        if os.path.exists(configfile):
            print(configfile)
            configparser.import_config(configfile)
            newconfig = config.import_teamocil(configparser.get())
            configparser.import_config(newconfig)
        else:
            sys.exit('File not found: %s' % configfile)

        config_format = prompt_choices('Convert to', choices=[
                                       'yaml', 'json'], default='yaml')

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
            '---------------------------------------------------------------')
        print(
            'Configuration import does its best to convert teamocil files.\n')
        if args.answer_yes or prompt_yes_no(
            'The new config *WILL* require adjusting afterwards. Save config?'
        ):
            dest = None
            while not dest:
                dest_prompt = prompt('Save to: ', os.path.abspath(
                    os.path.join(config_dir, 'myimport.%s' % config_format)))
                if os.path.exists(dest_prompt):
                    print('%s exists. Pick a new filename.' % dest_prompt)
                    continue

                dest = dest_prompt

            dest = os.path.abspath(os.path.relpath(os.path.expanduser(dest)))
            if args.answer_yes or prompt_yes_no('Write to %s?' % dest):
                buf = open(dest, 'w')
                buf.write(newconfig)
                buf.close()

                print('Saved to %s.' % dest)
        else:
            print(
                'tmuxp has examples in JSON and YAML format at <http://tmuxp.readthedocs.org/en/latest/examples.html>\n'
                'View tmuxp docs at <http://tmuxp.readthedocs.org/>'
            )
            sys.exit()


def command_import_tmuxinator(args):
    """Import tmuxinator config to tmuxp format."""
    if args.list:
            try:
                configs_in_user = config.in_dir(
                    tmuxinator_config_dir, extensions='yml')
            except OSError:
                configs_in_user = []
            configs_in_cwd = config.in_dir(
                config_dir=cwd_dir, extensions='yml')

            output = ''

            if not os.path.exists(tmuxinator_config_dir):
                output += '# %s: \n\tDirectory doesn\'t exist.\n' % tmuxinator_config_dir
            elif not configs_in_user:
                output += '# %s: \n\tNone found.\n' % tmuxinator_config_dir
            else:
                output += '# %s: \n\t%s\n' % (
                    config_dir, ', '.join(configs_in_user)
                )

            if configs_in_cwd:
                output += '# current directory:\n\t%s' % (
                    ', '.join(configs_in_cwd)
                )

            print(output)

    if args.config:
        configfile = os.path.abspath(os.path.relpath(
            os.path.expanduser(args.config)))
        configparser = kaptan.Kaptan(handler='yaml')

        if os.path.exists(configfile):
            print(configfile)
            configparser.import_config(configfile)
            newconfig = config.import_tmuxinator(configparser.get())
            configparser.import_config(newconfig)
        else:
            sys.exit('File not found: %s' % configfile)

        config_format = prompt_choices('Convert to', choices=[
                                       'yaml', 'json'], default='yaml')

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
            '---------------------------------------------------------------')
        print(
            'Configuration import does its best to convert tmuxinator files.\n')
        if args.answer_yes or prompt_yes_no(
            'The new config *WILL* require adjusting afterwards. Save config?'
        ):
            dest = None
            while not dest:
                dest_prompt = prompt('Save to: ', os.path.abspath(
                    os.path.join(config_dir, 'myimport.%s' % config_format)))
                if os.path.exists(dest_prompt):
                    print('%s exists. Pick a new filename.' % dest_prompt)
                    continue

                dest = dest_prompt

            dest = os.path.abspath(os.path.relpath(os.path.expanduser(dest)))
            if args.answer_yes or prompt_yes_no('Write to %s?' % dest):
                buf = open(dest, 'w')
                buf.write(newconfig)
                buf.close()

                print('Saved to %s.' % dest)
        else:
            print(
                'tmuxp has examples in JSON and YAML format at <http://tmuxp.readthedocs.org/en/latest/examples.html>\n'
                'View tmuxp docs at <http://tmuxp.readthedocs.org/>'
            )
            sys.exit()


def command_convert(args):
    """Convert tmuxp config to and from JSON and YAML."""

    try:
        configfile = args.config
    except exc.TmuxpException:
        print('Please enter a config')

    file_user = os.path.join(config_dir, configfile)
    file_cwd = os.path.join(cwd_dir, configfile)
    if os.path.exists(file_cwd) and os.path.isfile(file_cwd):
        fullfile = os.path.normpath(file_cwd)
        filename, ext = os.path.splitext(file_cwd)
    elif os.path.exists(file_user) and os.path.isfile(file_user):

        fullfile = os.path.normpath(file_user)
        filename, ext = os.path.splitext(file_user)
    else:
        logger.error('%s not found.' % configfile)
        return

    if 'json' in ext:
        if args.answer_yes or prompt_yes_no('convert to <%s> to yaml?' % (fullfile)):
            configparser = kaptan.Kaptan()
            configparser.import_config(configfile)
            newfile = fullfile.replace(ext, '.yaml')
            newconfig = configparser.export(
                'yaml', indent=2, default_flow_style=False
            )
            if args.answer_yes or prompt_yes_no('write config to %s?' % (newfile)):
                buf = open(newfile, 'w')
                buf.write(newconfig)
                buf.close()
                print('written new config to %s' % (newfile))
    elif 'yaml' in ext:
        if args.answer_yes or prompt_yes_no('convert to <%s> to json?' % (fullfile)):
            configparser = kaptan.Kaptan()
            configparser.import_config(configfile)
            newfile = fullfile.replace(ext, '.json')
            newconfig = configparser.export('json', indent=2)
            print(newconfig)
            if args.answer_yes or prompt_yes_no('write config to <%s>?' % (newfile)):
                buf = open(newfile, 'w')
                buf.write(newconfig)
                buf.close()
                print('written new config to <%s>.' % (newfile))


def command_attach_session(args):
    """Command to attach / switch client to a tmux session."""
    commands = []
    ctext = ' '.join(args.session_name)

    t = Server(
        socket_name=args.socket_name,
        socket_path=args.socket_path,
        colors=args.colors
    )

    try:
        session = next((s for s in t.sessions if s.get(
            'session_name') == ctext), None)
        if not session:
            raise exc.TmuxpException('Session not found.')
    except exc.TmuxpException as e:
        print(e)
        return

    if 'TMUX' in os.environ:
        del os.environ['TMUX']
        session.switch_client()
        print('Inside tmux client, switching client.')
    else:
        session.attach_session()
        print('Attaching client.')


def command_kill_session(args):
    """Command to kill a tmux session."""
    commands = []
    ctext = ' '.join(args.session_name)

    t = Server(
        socket_name=args.socket_name or None,
        socket_path=args.socket_path or None
    )

    try:
        session = next((s for s in t.sessions if s.get(
            'session_name') == ctext), None)
        if not session:
            raise exc.TmuxpException('Session not found.')
    except exc.TmuxpException as e:
        print(e)
        return

    try:
        session.kill_session()
        print("Killed session %s." % ctext)
    except exc.TmuxpException as e:
        logger.error(e)

def get_parser():
    """Return :py:class:`argparse.ArgumentParser` instance for CLI."""

    server_parser = argparse.ArgumentParser(add_help=False)

    # server_parser.add_argument(
        # '--log-level',
        # dest='log_level',
        # default='INFO',
        # metavar='log-level',
        # help='Log level e.g. INFO, DEBUG, ERROR'
    # )

    server_parser.add_argument(
        '-L', dest='socket_name',
        default=None,
        help='socket name of tmux server. Same as tmux.',
        metavar='socket-name'
    )

    server_parser.add_argument(
        '-S',
        dest='socket_path',
        default=None,
        help='socket path of tmux server. Same as tmux.',
        metavar='socket-path'
    )

    server_parser.add_argument(
        '-y',
        dest='answer_yes',
        default=None,
        help='Always answer yes.',
        action='store_true'
    )

    parser = argparse.ArgumentParser(
        description='Launch tmux workspace. '
                    'Help documentation: <http://tmuxp.rtfd.org>.',
        parents=[server_parser]
    )

    client_parser = argparse.ArgumentParser(add_help=False)
    colorsgroup = client_parser.add_mutually_exclusive_group()

    colorsgroup.add_argument(
        '-2',
        dest='colors',
        action='store_const',
        const=256,
        help='Force tmux to assume the terminal supports 256 colours.',
    )

    colorsgroup.add_argument(
        '-8',
        dest='colors',
        action='store_const',
        const=88,
        help='Like -2, but indicates that the terminal supports 88 colours.',
    )

    parser.set_defaults(colors=None)

    subparsers = parser.add_subparsers(
        title='commands',
        description='valid commands',
    )

    kill_session = subparsers.add_parser(
        'kill-session',
        parents=[server_parser],
        help='Kill tmux session by name.'
    )
    kill_session.set_defaults(callback=command_kill_session)

    kill_session.add_argument(
        dest='session_name',
        type=str,
        nargs='+',
        default=None,
        help='Name of session',
    ).completer = SessionCompleter

    attach_session = subparsers.add_parser(
        'attach-session',
        parents=[server_parser, client_parser],
        help='If run from outside tmux, create a new client in the current '
             'terminal and attach it. If used from inside, switch the current '
             'client.'
    )
    attach_session.set_defaults(callback=command_attach_session)

    attach_session.add_argument(
        dest='session_name',
        nargs='+',
        type=str,
        help='Name of session',
    ).completer = SessionCompleter

    freeze = subparsers.add_parser(
        'freeze',
        parents=[server_parser],
        help='Create a snapshot of a tmux session and save it to JSON or YAML.'
    )
    freeze.set_defaults(callback=command_freeze)

    freeze.add_argument(
        dest='session_name',
        type=str,
        nargs='+',
        help='Name of session',
    ).completer = SessionCompleter

    load = subparsers.add_parser(
        'load',
        parents=[server_parser, client_parser],
        help='Load a configuration from file. Attach the session. If session '
             'already exists, offer to attach instead.'
    )

    loadgroup = load.add_mutually_exclusive_group(required=True)
    loadgroup.add_argument(
        '--list', dest='list', action='store_true',
        help='List config files available',
    )

    loadgroup.add_argument(
        dest='config',
        type=str,
        nargs='?',
        help='List config available in working directory and config folder.'
    ).completer = ConfigFileCompleter(allowednames=('.yaml', '.json'), directories=False)
    load.set_defaults(callback=command_load)

    convert = subparsers.add_parser(
        'convert',
        help='Convert tmuxp config between YAML and JSON format.'
    )

    convert.add_argument(
        dest='config',
        type=str,
        default=None,
        help='Absolute or relative path to config file.'
    ).completer = ConfigFileCompleter(allowednames=('.yaml', '.json'), directories=False)

    convert.set_defaults(callback=command_convert)

    importparser = subparsers.add_parser(
        'import',
        help='Import configurations from teamocil and tmuxinator.'
    )
    importsubparser = importparser.add_subparsers(
        title='commands',
        description='valid commands',
        help='additional help'
    )

    import_teamocil = importsubparser.add_parser(
        'teamocil',
        help="Parse teamocil configurations into tmuxp format"
    )

    import_teamocilgroup = import_teamocil.add_mutually_exclusive_group(
        required=True
    )
    import_teamocilgroup.add_argument(
        '--list', dest='list', action='store_true',
        help='List configs in ~/.teamocil and current working directory.'
    )

    import_teamocilgroup.add_argument(
        dest='config',
        type=str,
        nargs='?',
        help='''\
        Checks current ~/.teamocil and current directory for yaml files.
        '''
    ).completer = TeamocilCompleter(allowednames=('.yml'), directories=False)
    import_teamocil.set_defaults(callback=command_import_teamocil)

    import_tmuxinator = importsubparser.add_parser(
        'tmuxinator',
        help="Parse teamocil configurations into tmuxp format"
    )

    import_tmuxinatorgroup = import_tmuxinator.add_mutually_exclusive_group(
        required=True)
    import_tmuxinatorgroup.add_argument(
        '--list', dest='list', action='store_true',
        help='List yaml configs in ~/.tmuxinator and current working directory.'
    )

    import_tmuxinatorgroup.add_argument(
        dest='config',
        type=str,
        nargs='?',
        help='''\
        Checks current ~/.tmuxinator and current directory for yaml files.
        '''
    ).completer = TmuxinatorCompleter(allowednames=('.yml'), directories=False)

    import_tmuxinator.set_defaults(callback=command_import_tmuxinator)

    # http://stackoverflow.com/questions/8521612/argparse-optional-subparser
    parser.add_argument(
        '-v', '--version', action='version',
        version='tmuxp %s' % __version__,
        help='Prints the tmuxp version',
    )

    return parser


def main():

    parser = get_parser()

    argcomplete.autocomplete(parser, always_complete_options=False)

    args = parser.parse_args()

    setup_logger(level=args.log_level.upper() if 'log_level' in args else 'INFO')

    try:
        util.has_required_tmux_version()
    except exc.TmuxpException as e:
        logger.error(e)
        sys.exit()

    util.oh_my_zsh_auto_title()

    t = Server(
        socket_name=args.socket_name,
        socket_path=args.socket_path,
        colors=args.colors
    )

    if args.callback is command_load:
        command_load(args)
    elif args.callback is command_convert:
        command_convert(args)
    elif args.callback is command_import_teamocil:
        command_import_teamocil(args)
    elif args.callback is command_import_tmuxinator:
        command_import_tmuxinator(args)
    elif args.callback is command_freeze:
        command_freeze(args)
    elif args.callback is command_attach_session:
        command_attach_session(args)
    elif args.callback is command_kill_session:
        command_kill_session(args)
    else:
        parser.print_help()
