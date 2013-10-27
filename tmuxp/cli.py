# -*- coding: utf8 - *-
"""
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
from . import config
from distutils.util import strtobool
from . import log, util, exc, WorkspaceBuilder, Server
import pkg_resources

__version__ = pkg_resources.require("tmuxp")[0].version

logger = logging.getLogger(__name__)

config_dir = os.path.expanduser('~/.tmuxp/')
cwd_dir = os.getcwd() + '/'
tmuxinator_config_dir = os.path.expanduser('~/.tmuxinator/')
teamocil_config_dir = os.path.expanduser('~/.teamocil/')


class ConfigCompleter(argcomplete.completers.FilesCompleter):

    def __call__(self, prefix, **kwargs):
        completion = argcomplete.completers.FilesCompleter.__call__(
            self, prefix, **kwargs
        )

        completion += [os.path.join(config_dir, c)
                       for c in config.in_dir(config_dir)]

        return completion


class TmuxinatorCompleter(argcomplete.completers.FilesCompleter):

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

    def __call__(self, prefix, **kwargs):
        completion = argcomplete.completers.FilesCompleter.__call__(
            self, prefix, **kwargs
        )

        teamocil_configs = config.in_dir(teamocil_config_dir, extensions='yml')
        completion += [os.path.join(teamocil_config_dir, f)
                       for f in teamocil_configs]

        return completion


def SessionCompleter(prefix, **kwargs):
    t = Server()
    return [s.get('session_name') for s in t._sessions if s.get('session_name').startswith(prefix)]


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is one of "yes" or "no".

    License MIT: http://code.activestate.com/recipes/577058/
    """
    valid = {"yes": "yes",   "y": "yes",  "ye": "yes",
             "no": "no",     "n": "no"}
    if default == None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return strtobool(default)
        elif choice in valid.keys():
            return strtobool(valid[choice])
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


def setupLogger(logger=None, level='INFO'):
    '''setup logging for CLI use.

    :param logger: instance of logger
    :type logger: :py:class:`Logger`
    '''
    if not logger:
        logger = logging.getLogger()
    if not logger.handlers:
        channel = logging.StreamHandler()
        channel.setFormatter(log.LogFormatter())
        logger.setLevel(level)
        logger.addHandler(channel)


def startup(config_dir):
    ''' Initialize CLI.

    :param config_dir: Config directory to search
    :type config_dir: string
    '''

    if not os.path.exists(config_dir):
        os.makedirs(config_dir)


def build_workspace(config_file, args):
    ''' build config workspace.

    :param config_file: full path to config file
    :param type: string
    '''
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
            if query_yes_no('Already inside TMUX, load session?'):
                del os.environ['TMUX']
                os.execl(tmux_bin, 'tmux', 'switch-client', '-t', sconfig[
                         'session_name'])

        os.execl(tmux_bin, 'tmux', 'attach-session', '-t', sconfig[
                 'session_name'])
    except exc.TmuxSessionExists as e:
        attach_session = query_yes_no(e.message + ' Attach?')

        if 'TMUX' in os.environ:
            del os.environ['TMUX']
            os.execl(tmux_bin, 'tmux', 'switch-client', '-t', sconfig[
                     'session_name'])

        if attach_session:
            os.execl(tmux_bin, 'tmux', 'attach-session', '-t', sconfig[
                     'session_name'])
        return


def subcommand_load(args):
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
                print configfile
            else:
                print('No tmuxp configs found in current directory.')
        else:
            configfile = args.config
        file_user = os.path.join(config_dir, configfile)
        file_cwd = os.path.join(cwd_dir, configfile)
        if os.path.exists(file_cwd) and os.path.isfile(file_cwd):
            build_workspace(file_cwd, args)
        elif os.path.exists(file_user) and os.path.isfile(file_user):
            build_workspace(file_user, args)
        else:
            logger.error('%s not found.' % configfile)


def subcommand_import_teamocil(args):
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

    if args.config:
        configfile = os.path.relpath(args.config)
        configparser = kaptan.Kaptan(handler='yaml')
        configparser.import_config(configfile)

        newconfig = config.import_teamocil(configparser.get())

        newconfig = configparser.import_config(newconfig)
        newconfig = configparser.export(
            'yaml', indent=2, default_flow_style=False
        )

        print(newconfig)


def subcommand_import_tmuxinator(args):
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
        configfile = os.path.relpath(args.config)
        configparser = kaptan.Kaptan(handler='yaml')
        configparser.import_config(configfile)

        newconfig = config.import_tmuxinator(configparser.get())

        newconfig = configparser.import_config(newconfig)
        newconfig = configparser.export(
            'yaml', indent=2, default_flow_style=False
        )

        print(newconfig)


def subcommand_convert(args):
    if args.config:
        if '.' in args.config:
            args.config.remove('.')
            if config.in_cwd():
                args.config.append(config.in_cwd()[0])
            else:
                print('No tmuxp configs found in current directory.')

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
            if query_yes_no('convert to <%s> to yaml?' % (fullfile)):
                configparser = kaptan.Kaptan()
                configparser.import_config(configfile)
                newfile = fullfile.replace(ext, '.yaml')
                newconfig = configparser.export(
                    'yaml', indent=2, default_flow_style=False
                )
                if query_yes_no('write config to %s?' % (newfile)):
                    buf = open(newfile, 'w')
                    buf.write(newconfig)
                    buf.close()
                    print ('written new config to %s' % (newfile))
        elif 'yaml' in ext:
            if query_yes_no('convert to <%s> to json?' % (fullfile)):
                configparser = kaptan.Kaptan()
                configparser.import_config(configfile)
                newfile = fullfile.replace(ext, '.json')
                newconfig = configparser.export('json', indent=2)
                print(newconfig)
                if query_yes_no('write config to <%s>?' % (newfile)):
                    buf = open(newfile, 'w')
                    buf.write(newconfig)
                    buf.close()
                    print ('written new config to <%s>.' % (newfile))


def subcommand_attach_session(args):
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


def subcommand_kill_session(args):
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


def cli_parser():

    parser = argparse.ArgumentParser(
        description='''\
        Launch tmux workspace. Help documentation: <http://tmuxp.rtfd.org>.
        ''',
    )

    subparsers = parser.add_subparsers(title='subcommands',
                                       description='valid subcommands',
                                       help='additional help')

    kill_session = subparsers.add_parser('kill-session')
    kill_session.set_defaults(callback=subcommand_kill_session)

    kill_session.add_argument(
        dest='session_name',
        type=str,
        default=None,
    ).completer = SessionCompleter

    attach_session = subparsers.add_parser('attach-session')
    attach_session.set_defaults(callback=subcommand_attach_session)

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
    ).completer = ConfigCompleter(allowednames=('.yaml', '.json'), directories=False)
    load.set_defaults(callback=subcommand_load)

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
    ).completer = ConfigCompleter(allowednames=('.yaml', '.json'), directories=False)

    convert.set_defaults(callback=subcommand_convert)

    importparser = subparsers.add_parser('import')
    importsubparser = importparser.add_subparsers(title='subcommands',
                                                  description='valid subcommands',
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
    import_teamocil.set_defaults(callback=subcommand_import_teamocil)

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

    import_tmuxinator.set_defaults(callback=subcommand_import_tmuxinator)

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

    parser = cli_parser()

    argcomplete.autocomplete(parser, always_complete_options=False)

    args = parser.parse_args()

    setupLogger(level=args.log_level.upper())

    try:
        util.version()
    except Exception as e:
        logger.error(e)
        sys.exit()

    util.oh_my_zsh_auto_title()

    if args.callback is subcommand_load:
        subcommand_load(args)
    elif args.callback is subcommand_convert:
        subcommand_convert(args)
    elif args.callback is subcommand_import_teamocil:
        subcommand_import_teamocil(args)
    elif args.callback is subcommand_import_tmuxinator:
        subcommand_import_tmuxinator(args)
    elif args.callback is subcommand_attach_session:
        subcommand_attach_session(args)
    elif args.callback is subcommand_kill_session:
        subcommand_kill_session(args)
    else:
        parser.print_help()
