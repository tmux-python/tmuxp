# -*- coding: utf8 - *-
"""
    tmuxp.config
    ~~~~~~~~~~~~

    tmuxp helps you manage tmux workspaces.

    :copyright: Copyright 2013 Tony Narlock.
    :license: BSD, see LICENSE for details
"""


def expand_config(config):
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

    shell_command: 'string' => shell_command: list('string')

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
        config['windows'] = [expand_config(window)
                             for window in config['windows']]
    if 'panes' in config:
        config['panes'] = [expand_config(pane) for pane in config['panes']]

    return config


def trickledown_config(config):
    '''Trickle down / inherit config values

    This will only work if config has been expand with ConfigExpand()

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
