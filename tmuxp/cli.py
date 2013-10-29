# -*- coding: utf8 - *-
"""Command line tool for managing tmux workspaces and tmuxp configurations.

tmuxp.cli
~~~~~~~~~

:copyright: Copyright 2013 Tony Narlock.
:license: BSD, see LICENSE for details


prompt, prompt_bool, prompt_choices
LICENSE: https://github.com/techniq/flask-script/blob/master/LICENSE

"""

import os
import sys
import argparse
import argcomplete
import logging
import kaptan
from . import config
from distutils.util import strtobool
from . import log, util, exc, WorkspaceBuilder, Server
from .util import ascii_lowercase, input
import pkg_resources

__version__ = pkg_resources.require("tmuxp")[0].version

logger = logging.getLogger(__name__)

config_dir = os.path.expanduser('~/.tmuxp/')
cwd_dir = os.getcwd() + '/'
tmuxinator_config_dir = os.path.expanduser('~/.tmuxinator/')
teamocil_config_dir = os.path.expanduser('~/.teamocil/')


def prompt(name, default=None):
    """Return user input from command line.

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
    """
    Return user input from command line and converts to boolean value.

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
    return prompt_bool(name, default=default)


def prompt_choices(name, choices, default=None, resolve=ascii_lowercase,
                   no_choice=('none',)):
    """
    Return user input from command line from set of provided choices.

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

    """ argcomplete completer for tmuxp files. """

    def __call__(self, prefix, **kwargs):
        completion = argcomplete.completers.FilesCompleter.__call__(
            self, prefix, **kwargs
        )

        completion += [os.path.join(config_dir, c)
                       for c in config.in_dir(config_dir)]

        return completion


class TmuxinatorCompleter(argcomplete.completers.FilesCompleter):

    """ argcomplete completer for Tmuxinator files. """

    def __call__(self, prefix, **kwargs):
        completion = argcomplete.completers.FilesCompleter.__call__(
            self, prefix, **kwargs
        )

        tmuxinator_configs = config.in_dir(
            tmuxinator_config_dir, extensions='yml')
        completion += [os.path.join(tmuxinator_config_dir, f)
                       for f in tmuxinator_configs]

        return completion


class TeamocilCompleter(argcomplete.completers.FilesCompleter):

    """ argcomplete completer for Teamocil files. """

    def __call__(self, prefix, **kwargs):
        completion = argcomplete.completers.FilesCompleter.__call__(
            self, prefix, **kwargs
        )

        teamocil_configs = config.in_dir(teamocil_config_dir, extensions='yml')
        completion += [os.path.join(teamocil_config_dir, f)
                       for f in teamocil_configs]

        return completion


def SessionCompleter(prefix, **kwargs):
    """ Return list of session names for argcomplete completer. """
    t = Server()
    return [s.get('session_name') for s in t._sessions
            if s.get('session_name').startswith(prefix)]


def setup_logger(logger=None, level='INFO'):
    """Setup logging for CLI use.

    :param logger: instance of logger
    :type logger: :py:class:`Logger`

    """
    if not logger:
        logger = logging.getLogger()
    if not logger.handlers:
        channel = logging.StreamHandler()
        channel.setFormatter(log.LogFormatter())
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
    """ Build config workspace.

    :param config_file: full path to config file
    :param type: string

    """
    logger.info('building %s.' % config_file)

    sconfig = kaptan.Kaptan()
    sconfig = sconfig.import_config(config_file).get()
    sconfig = config.expand(sconfig)
    sconfig = config.trickle(sconfig)

    t = Server(
        socket_name=args.socket_name,
        socket_path=args.socket_path
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
            if prompt_yes_no('Already inside TMUX, load session?'):
                del os.environ['TMUX']
                os.execl(tmux_bin, 'tmux', 'switch-client', '-t', sconfig[
                         'session_name'])

        os.execl(tmux_bin, 'tmux', 'attach-session', '-t', sconfig[
                 'session_name'])
    except exc.TmuxSessionExists as e:
        attach_session = prompt_yes_no(e.message + ' Attach?')

        if 'TMUX' in os.environ:
            del os.environ['TMUX']
            os.execl(tmux_bin, 'tmux', 'switch-client', '-t',
                     sconfig['session_name'])

        if attach_session:
            os.execl(tmux_bin, 'tmux', 'attach-session', '-t',
                     sconfig['session_name'])
        return


def command_load(args):
    """ Load a session from a tmuxp session file. """
    if args.list:
        startup(config_dir)
        configs_in_user = config.in_dir(config_dir)
        configs_in_cwd = config.in_cwd()

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

    elif args.config:
        if '.' == args.config:
            if config.in_cwd():
                configfile = config.in_cwd()[0]
            else:
                print('No tmuxp configs found in current directory.')
        else:
            configfile = args.config
        file_user = os.path.join(config_dir, configfile)
        file_cwd = os.path.join(cwd_dir, configfile)
        if os.path.exists(file_cwd) and os.path.isfile(file_cwd):
            load_workspace(file_cwd, args)
        elif os.path.exists(file_user) and os.path.isfile(file_user):
            load_workspace(file_user, args)
        else:
            logger.error('%s not found.' % configfile)


def command_import_teamocil(args):
    """ Import teamocil config to tmuxp format. """

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
        configfile = os.path.abspath(os.path.relpath(args.config))
        configparser = kaptan.Kaptan(handler='yaml')

        if os.path.exists(configfile):
            print(configfile)
            configparser.import_config(configfile)
        else:
            sys.exit('File not found: %s' % configfile)

        newconfig = config.import_teamocil(configparser.get())

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
        if prompt_yes_no(
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

            dest = os.path.abspath(os.path.relpath(dest))
            if prompt_yes_no('Write to %s?' % dest):
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
    """ Import tmuxinator config to tmuxp format. """
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
        configfile = os.path.abspath(os.path.relpath(args.config))
        configparser = kaptan.Kaptan(handler='yaml')

        if os.path.exists(configfile):
            print(configfile)
            configparser.import_config(configfile)
        else:
            sys.exit('File not found: %s' % configfile)

        newconfig = config.import_tmuxinator(configparser.get())

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
        if prompt_yes_no(
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

            dest = os.path.abspath(os.path.relpath(dest))
            if prompt_yes_no('Write to %s?' % dest):
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
    """ Convert tmuxp config to and from JSON and YAML. """

    try:
        configfile = args.config
    except Exception:
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
        if prompt_yes_no('convert to <%s> to yaml?' % (fullfile)):
            configparser = kaptan.Kaptan()
            configparser.import_config(configfile)
            newfile = fullfile.replace(ext, '.yaml')
            newconfig = configparser.export(
                'yaml', indent=2, default_flow_style=False
            )
            if prompt_yes_no('write config to %s?' % (newfile)):
                buf = open(newfile, 'w')
                buf.write(newconfig)
                buf.close()
                print('written new config to %s' % (newfile))
    elif 'yaml' in ext:
        if prompt_yes_no('convert to <%s> to json?' % (fullfile)):
            configparser = kaptan.Kaptan()
            configparser.import_config(configfile)
            newfile = fullfile.replace(ext, '.json')
            newconfig = configparser.export('json', indent=2)
            print(newconfig)
            if prompt_yes_no('write config to <%s>?' % (newfile)):
                buf = open(newfile, 'w')
                buf.write(newconfig)
                buf.close()
                print('written new config to <%s>.' % (newfile))


def command_attach_session(args):
    """ Command to attach / switch client to a tmux session."""
    commands = []
    ctext = args.session_name

    t = Server(
        socket_name=args.socket_name or None,
        socket_path=args.socket_path or None
    )
    try:
        session = next((s for s in t.sessions if s.get(
            'session_name') == ctext), None)
        if not session:
            raise Exception('Session not found.')
    except Exception as e:
        print(e.message[0])
        return

    if 'TMUX' in os.environ:
        del os.environ['TMUX']
        session.switch_client()
        print('Inside tmux client, switching client.')
    else:
        session.attach_session()
        print('Attaching client.')


def command_kill_session(args):
    """ Command to kill a tmux session."""
    commands = []
    ctext = args.session_name

    t = Server(
        socket_name=args.socket_name or None,
        socket_path=args.socket_path or None
    )

    try:
        session = next((s for s in t.sessions if s.get(
            'session_name') == ctext), None)
        if not session:
            raise Exception('Session not found.')
    except Exception as e:
        print(e.message[0])
        return

    try:
        session.kill_session()
    except Exception as e:
        logger.error(e)


def get_parser():
    """ Return :py:class:`argparse.ArgumentParser` instance for CLI. """

    parser = argparse.ArgumentParser(
        description='''\
        Launch tmux workspace. Help documentation: <http://tmuxp.rtfd.org>.
        ''',
    )

    subparsers = parser.add_subparsers(title='commands',
                                       description='valid commands',
                                       help='additional help')

    kill_session = subparsers.add_parser('kill-session')
    kill_session.set_defaults(callback=command_kill_session)

    kill_session.add_argument(
        dest='session_name',
        type=str,
        default=None,
    ).completer = SessionCompleter

    attach_session = subparsers.add_parser('attach-session')
    attach_session.set_defaults(callback=command_attach_session)

    attach_session.add_argument(
        dest='session_name',
        type=str,
    ).completer = SessionCompleter

    load = subparsers.add_parser('load')

    loadgroup = load.add_mutually_exclusive_group(required=True)
    loadgroup.add_argument(
        '--list', dest='list', action='store_true',
        help='List config files available',
    )

    loadgroup.add_argument(
        dest='config',
        type=str,
        nargs='?',
        help='''\
        List of config files to launch session from.

        Checks current working directory (%s) then $HOME/.tmuxp directory (%s).

            $ tmuxp .

        will check launch a ~/.pullv.yaml / ~/.pullv.json from the cwd.
        will also check for any ./*.yaml and ./*.json.
        ''' % (cwd_dir + '/', config_dir),
    ).completer = ConfigFileCompleter(allowednames=('.yaml', '.json'), directories=False)
    load.set_defaults(callback=command_load)

    convert = subparsers.add_parser('convert')

    convert.add_argument(
        dest='config',
        type=str,
        default=None,
        help='''\
        Checks current working directory (%s) then $HOME/.tmuxp directory (%s).

            $ tmuxp .

        will check launch a ~/.pullv.yaml / ~/.pullv.json from the cwd.
        will also check for any ./*.yaml and ./*.json.
        ''' % (cwd_dir + '/', config_dir)
    ).completer = ConfigFileCompleter(allowednames=('.yaml', '.json'), directories=False)

    convert.set_defaults(callback=command_convert)

    importparser = subparsers.add_parser('import')
    importsubparser = importparser.add_subparsers(title='commands',
                                                  description='valid commands',
                                                  help='additional help')

    import_teamocil = importsubparser.add_parser('teamocil')

    import_teamocilgroup = import_teamocil.add_mutually_exclusive_group(
        required=True)
    import_teamocilgroup.add_argument(
        '--list', dest='list', action='store_true',
        help='List yaml configs in ~/.teamocil and current working directory.'
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

    import_tmuxinator = importsubparser.add_parser('tmuxinator')

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

    parser.add_argument('--log-level', dest='log_level', default='INFO',
                        metavar='log-level',
                        help='Log level e.g. INFO, DEBUG, ERROR')

    parser.add_argument('-L', dest='socket_name', default=None,
                        metavar='socket-name')

    parser.add_argument('-S', dest='socket_path', default=None,
                        metavar='socket-path')

    # http://stackoverflow.com/questions/8521612/argparse-optional-subparser
    parser.add_argument(
        '-v', '--version', action='version',
        version='tmuxp %s' % __version__,
        help='Prints the tmuxp version')

    return parser


def main():

    parser = get_parser()

    argcomplete.autocomplete(parser, always_complete_options=False)

    args = parser.parse_args()

    setup_logger(level=args.log_level.upper())

    try:
        util.version()
    except Exception as e:
        logger.error(e)
        sys.exit()

    util.oh_my_zsh_auto_title()

    if args.callback is command_load:
        command_load(args)
    elif args.callback is command_convert:
        command_convert(args)
    elif args.callback is command_import_teamocil:
        command_import_teamocil(args)
    elif args.callback is command_import_tmuxinator:
        command_import_tmuxinator(args)
    elif args.callback is command_attach_session:
        command_attach_session(args)
    elif args.callback is command_kill_session:
        command_kill_session(args)
    else:
        parser.print_help()
