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
    if args.list_configs:
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

    elif args.configs:
        if '.' in args.configs:
            args.configs.remove('.')
            if config.in_cwd():
                args.configs.append(config.in_cwd()[0])
            else:
                print('No tmuxp configs found in current directory.')

        for configfile in args.configs:
            file_user = os.path.join(config_dir, configfile)
            file_cwd = os.path.join(cwd_dir, configfile)
            if os.path.exists(file_cwd) and os.path.isfile(file_cwd):
                build_workspace(file_cwd, args)
            elif os.path.exists(file_user) and os.path.isfile(file_user):
                build_workspace(file_user, args)
            else:
                logger.error('%s not found.' % configfile)


def subcommand_attach_session(args):
    commands = []
    try:
        ctext = args.session_name[0]
    except IndexError as e:
        return

    t = Server()
    try:
        session = [s for s in t.sessions if s.get('session_name') == ctext][0]
    except IndexError as e:
        print('Session not found.')
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
    ctext = args.session_name[0]

    t = Server()
    sessions = [s for s in t.sessions if s.get('session_name') == ctext]

    if (len(sessions) == 1):
        proc = sessions[0].kill_session()
        if proc.stderr:
            print(proc.stderr)

        print(proc.stdout)


def cli_parser():

    parser = argparse.ArgumentParser(
        description='''\
        Launch tmux workspace. Help documentation: <http://tmuxp.rtfd.org>.
        ''',
    )

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title='subcommands',
                                       description='valid subcommands',
                                       help='additional help')

    kill_session = subparsers.add_parser('kill-session')
    kill_session.set_defaults(callback=subcommand_kill_session)

    kill_session.add_argument(
        dest='session_name',
        nargs='*',
        type=str,
        default=None,
    )

    attach_session = subparsers.add_parser('attach-session')
    attach_session.set_defaults(callback=subcommand_attach_session)

    attach_session.add_argument(
        dest='session_name',
        nargs='*',
        type=str,
        default=None,
    )

    load = subparsers.add_parser('load')

    load.add_argument(
        '-l', '--list', dest='list_configs', action='store_true',
        help='List config files available')

    load.add_argument(
        dest='configs',
        nargs='*',
        type=str,
        default=None,
        help='''\
        List of config files to launch session from.

        Checks current working directory (%s) then $HOME/.tmuxp directory (%s).

            $ tmuxp .

        will check launch a ~/.pullv.yaml / ~/.pullv.json from the cwd.
        ''' % (cwd_dir + '/', config_dir)
    )
    load.set_defaults(callback=subcommand_load)

    parser.add_argument('--log-level', dest='log_level', default='INFO',
                        metavar='log-level',
                        help='Log level e.g. INFO, DEBUG, ERROR')

    parser.add_argument('-L', dest='socket_name', default=None,
                        metavar='socket-name')

    parser.add_argument('-S', dest='socket_path', default=None,
                        metavar='socket-path')

    parser.add_argument(
        '-v', '--version', dest='version', action='store_true',
        help='Prints the tmuxp version')

    return parser


def main():

    parser = cli_parser()

    args = parser.parse_args()

    setupLogger(level=args.log_level.upper())
    try:
        util.version()
    except Exception as e:
        logger.error(e)
        sys.exit()

    if args.callback is subcommand_load:
        subcommand_load(args)
    elif args.callback is subcommand_attach_session:
        subcommand_attach_session(args)
    elif args.callback is subcommand_kill_session:
        subcommand_kill_session(args)
    else:
        if args.version:
            print('tmuxp %s' % __version__)

        parser.print_help()


def complete(cline, cpoint):

    parser = argparse.ArgumentParser()
    parser.add_argument('-L', dest='socket_name', default=None,
                        metavar='socket-name')

    parser.add_argument('-S', dest='socket_path', default=None,
                        metavar='socket-path')

    parser.add_argument(
        dest='ctexta',
        nargs='*',
        type=str,
        default=None,
    )

    args = parser.parse_args()
    ctext = cline.replace('tmuxp ', '')

    commands = []
    commands.extend(['attach-session', 'kill-session', 'load'])

    commands = [c for c in commands if ctext in c]

    if args.socket_path:
        ctext = ctext.replace(args.socket_path or None, '')

    if args.socket_name:
        ctext = ctext.replace(args.socket_name or None, '')

    t = Server(
        # socket_name=args.socket_name or None,
        # socket_path=args.socket_path or None
    )

    def session_complete(command, commands, ctext):
        if ctext.startswith(command + ' '):
            commands[:] = []
            ctext_subargs = ctext.replace(command + ' ', '')

            sessions = [s.get('session_name') for s in t._sessions]
            commands.extend([c for c in sessions if ctext_subargs in c])

            # commands = [c for c in commands if ctext_subcommand_args in c]
            # commands = [c for c in commands if c.startswith(ctext_subargs)]

    def config_complete(command, commands, ctext):
        if ctext.startswith(command + ' '):
            commands[:] = []
            ctext_subargs = ctext.replace(command + ' ', '')
            configs = []
            configs += ['./' + c for c in config.in_cwd()]
            # configs += config.in_cwd()
            configs += [os.path.join(config_dir, c)
                        for c in config.in_dir(config_dir)]
            # configs += config.in_dir(config_dir)
            configs += ['./' + c for c in config.in_dir(cwd_dir)]
            # configs += config.in_dir(cwd_dir)
            commands += [c for c in configs if c.startswith(ctext_subargs)]

    session_complete('attach-session', commands, ctext)
    session_complete('kill-session', commands, ctext)
    config_complete('load', commands, ctext)

    print(' \n'.join(commands))
