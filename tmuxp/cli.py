# -*- coding: utf8 - *-
"""
    tmuxp.cli
    ~~~~~~~~~

    :copyright: Copyright 2013 Tony Narlock.
    :license: BSD, see LICENSE for details
"""

import os
import argparse
import logging
import kaptan
import config
from . import log, exc, WorkspaceBuilder, Server

logger = logging.getLogger(__name__)


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


def build_workspace(config_file):
    ''' build config workspace.

    :param config_file: full path to config file
    :param type: string
    '''
    logger.info('building %s.' % config_file)

    sconfig = kaptan.Kaptan()
    sconfig = sconfig.import_config(config_file).get()

    t = Server()
    try:
        builder = WorkspaceBuilder(sconf=sconfig, server=t)
    except exc.EmptyConfigException:
        logger.error('%s is empty or parsed no config data' % config_file)

    try:
        builder.build()
    except exc.TmuxSessionExists as e:
        logger.error(e.message)
        return

    window_count = len(session._windows)  # current window count
    for w, wconf in builder.iter_create_windows(session):

        window_pane_count = len(w._panes)
        for p in builder.iter_create_panes(w, wconf):
            p = p

        w.set_window_option('main-pane-height', 50)
        w.select_layout(wconf['layout'])

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
        # todo: implement support for $ tmux .
        # todo: pass thru -L socket-name, -S socket-path

        for configfile in args.configs:
            file_user = os.path.join(config_dir, configfile)
            file_cwd = os.path.join(cwd_dir, configfile)
            if os.path.exists(file_cwd):
                build_workspace(file_cwd)
            if os.path.exists(file_user):
                build_workspace(file_user)
            else:
                logger.error('%s not found.' % configfile)
    else:
        parser.print_help()
