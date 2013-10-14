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
import config
from . import log

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

        output = '\n'

        if not configs_in_user:
            output += '# %s: \n\tNone found.\n' % config_dir
        else:
            output += '# %s: \n\t%s\n' % (
                config_dir, ', '.join(configs_in_user)
            )

        if not configs_in_cwd:
            output += '# current directory: \n\tNone found.\n'
        else:
            output += '# current directory:\n\t%s' % (
                ', '.join(configs_in_cwd)
            )

        logger.info(output)
    else:
        logger.info(parser.print_help())
