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
import config
from distutils.util import strtobool
from . import log, exc, WorkspaceBuilder, Server

logger = logging.getLogger(__name__)


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is one of "yes" or "no".

    License MIT: http://code.activestate.com/recipes/577058/
    """
    valid = {"yes":"yes",   "y":"yes",  "ye":"yes",
             "no":"no",     "n":"no"}
    if default == None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while 1:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return strtobool(default)
        elif choice in valid.keys():
            return strtobool(valid[choice])
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "\
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

    t = Server()

    if args.socket_name:
        print('socket_name %s' % args.socket_name)
        t.socket_name = args.socket_name

    if args.socket_path:
        print('socket_path %s' % args.socket_path)
        t.socket_path = args.socket_path

    try:
        builder = WorkspaceBuilder(sconf=sconfig, server=t)
    except exc.EmptyConfigException:
        logger.error('%s is empty or parsed no config data' % config_file)
        return

    try:
        builder.build()
        os.execl('/usr/local/bin/tmux', 'tmux', 'attach-session', '-t', sconfig['session_name'])
    except exc.TmuxSessionExists as e:
        attach_session = query_yes_no(e.message + ' attach?')

        if attach_session:
            os.execl('/usr/local/bin/tmux', 'tmux', 'attach-session', '-t', sconfig['session_name'])
        return


def main():
    config_dir = os.path.expanduser('~/.tmuxp/')
    cwd_dir = os.getcwd() + '/'

    parser = argparse.ArgumentParser(
        description='''\
        Launch tmux workspace. Help documentation: <http://tmuxp.rtfd.org>.
        ''',
    )

    parser.add_argument(
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

    parser.add_argument('-L', dest='socket_name', default=None,
                        metavar='socket-name')

    parser.add_argument('-S', dest='socket_path', default=None,
                        metavar='socket-path')

    parser.add_argument('-l', '--list', dest='list_configs', action='store_true',
                        help='List config files available')
    parser.add_argument('--log-level', dest='log_level', default='INFO',
                        help='Log level')

    args = parser.parse_args()

    setupLogger(level=args.log_level.upper())

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
            args.configs.append(config.in_cwd()[0])

        for configfile in args.configs:
            file_user = os.path.join(config_dir, configfile)
            file_cwd = os.path.join(cwd_dir, configfile)
            if os.path.exists(file_cwd) and os.path.isfile(file_cwd):
                build_workspace(file_cwd, args)
            elif os.path.exists(file_user) and os.path.isfile(file_user):
                build_workspace(file_user, args)
            else:
                logger.error('%s not found.' % configfile)
    else:
        parser.print_help()


def complete(cline, cpoint):

    config_dir = os.path.expanduser('~/.tmuxp/')
    cwd_dir = os.getcwd() + '/'

    commands = []
    commands += config.in_dir(config_dir)
    commands += config.in_cwd()

    ctext = cline.replace('tmuxp ', '')
    commands = [c for c in commands if ctext in c]

    print(' \n'.join(commands))
