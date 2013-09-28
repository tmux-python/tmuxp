# -*- coding: utf8 - *-
"""
    tmuxp.config
    ~~~~~~~~~~~~

    tmuxp helps you manage tmux workspaces.

    :copyright: Copyright 2013 Tony Narlock.
    :license: BSD, see LICENSE for details
"""


def _expand_shell_command(c):
    '''any config section, session, window, pane that can
    contain the 'shell_command' value
    '''
    if ('shell_command' in c and
            isinstance(c['shell_command'], basestring)):
            c['shell_command'] = [c['shell_command']]

    if ('shell_command_before' in c and
            isinstance(c['shell_command_before'], basestring)):
            c['shell_command_before'] = [c['shell_command_before']]

    return c


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

    config = _expand_shell_command(config)
    for window in config['windows']:
        window = _expand_shell_command(window)
        window['panes'] = [_expand_shell_command(
            pane) for pane in window['panes']]

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

    if 'shell_command_before' in config:
        assert isinstance(config['shell_command_before'], list)
        session_shell_command_before = config['shell_command_before']
    else:
        session_shell_command_before = []

    for windowconfig in config['windows']:

        if 'shell_command_before' in windowconfig:
            window_shell_command_before = windowconfig['shell_command_before']
        else:
            window_shell_command_before = []

        for paneconfig in windowconfig['panes']:

            if 'shell_command_before' in paneconfig:
                pane_shell_command_before += paneconfig['shell_command_before']
            else:
                pane_shell_command_before = []

            if 'shell_command' not in paneconfig:
                paneconfig['shell_command'] = list()

            paneconfig['shell_command'] = session_shell_command_before + \
                window_shell_command_before + \
                pane_shell_command_before + paneconfig['shell_command']

    return config
