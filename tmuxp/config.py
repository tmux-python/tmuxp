# -*- coding: utf8 - *-
"""
    tmuxp.config
    ~~~~~~~~~~~~

    tmuxp helps you manage tmux workspaces.

    :copyright: Copyright 2013 Tony Narlock.
    :license: BSD, see LICENSE for details
"""

from __future__ import absolute_import, division, print_function, with_statement
import os
import logging

logger = logging.getLogger(__name__)


def is_config_file(filename, extensions=['.yaml', '.json', '.ini', '.py']):
    ''' only pull configs with correct name.

    :param filename: filename to check (e.g. ``mysession.json``).
    :type filename: string
    :param extensions: filetypes to check (e.g. ``['.yaml', '.json']``).
    :rtype: bool
    '''
    return any(filename.endswith(e) for e in extensions)


def in_dir(config_dir=os.path.expanduser('~/.tmuxp')):
    '''find configs in config_dir and current dir

    :param config_dir: directory to search
    :type config_dir: string
    :rtype: list
    '''
    configs = []

    for (dirpath, dirname, filenames) in os.walk(config_dir):
        for filename in filenames:
            if is_config_file(filename):
                configs.append(filename)

    return configs

def inline(config):
    ''' opposite of :meth:`config.expand`. Where possible, inline.
    '''

    if ('shell_command' in config and isinstance(config['shell_command'], list) and len(config['shell_command']) == 1):
        config['shell_command'] = config['shell_command'][0]
    if ('shell_command_before' in config and isinstance(config['shell_command_before'], list) and len(config['shell_command_before']) == 1):
        config['shell_command_before'] = config['shell_command_before'][0]

    # recurse into window and pane config items
    if 'windows' in config:
        config['windows'] = [inline(window)
                             for window in config['windows']]
    if 'panes' in config:
        config['panes'] = [inline(pane) for pane in config['panes']]

    return config


def expand(config):
    '''Expand configuration into full form. Enables shorthand forms for tmuxp
    config.

    This is necessary to keep the code in the :class:`Builder` clean and also
    allow for neat, short-hand configurations.

    As a simple example, internally, tmuxp expects that config options
    like ``shell_command`` are a list (array)::

        'shell_command': ['htop']

    tmuxp configs allow for it to be simply a string::

        'shell_command': 'htop'

    Kaptan will load JSON/YAML/INI files into python dicts for you.
    :param config: the configuration for the session
    :type config: dict

    iterate through session, windows, and panes for ``shell_command``, if
    it is a string, turn to list.

    :param config: the session configuration
    :type config: dict
    '''

    '''any config section, session, window, pane that can
    contain the 'shell_command' value
    '''
    if ('shell_command' in config and isinstance(config['shell_command'], basestring)):
        config['shell_command'] = [config['shell_command']]

    if ('shell_command_before' in config and isinstance(config['shell_command_before'], basestring)):
        config['shell_command_before'] = [config['shell_command_before']]

    # recurse into window and pane config items
    if 'windows' in config:
        config['windows'] = [expand(window)
                             for window in config['windows']]
    if 'panes' in config:
        config['panes'] = [expand(pane) for pane in config['panes']]

    return config


def trickle(config):
    '''Trickle down / inherit config values

    This will only work if config has been expanded to full form with
    :meth:`config.expand`.

    tmuxp allows certain commands to be default at the session, window
    level. shell_command_before trickles down and prepends the
    ``shell_command`` for the pane.

    :param config: the session configuration
    :type config: dict
    '''

    '''
    prepends a pane's ``shell_command`` list with the window and sessions'
    ``shell_command_before``.
    '''

    for windowconfig in config['windows']:
        for paneconfig in windowconfig['panes']:
            commands_before = config[
                'shell_command_before'] if 'shell_command_before' in config else []
            commands_before.extend(windowconfig[
                                   'shell_command_before']) if 'shell_command_before' in windowconfig else None
            commands_before.extend(paneconfig[
                                   'shell_command_before']) if 'shell_command_before' in paneconfig else None

            if 'shell_command' not in paneconfig:
                paneconfig['shell_command'] = list()

            commands_before.extend(paneconfig[
                                   'shell_command']) if paneconfig['shell_command'] else None
            paneconfig['shell_command'] = commands_before

    return config
