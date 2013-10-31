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
from . import exc
from .util import basestring

logger = logging.getLogger(__name__)


def check_consistency(sconf):
    '''Verify the consistency of the config file.

    Config files in tmuxp are met to import into :py:mod:`dict`.
    '''

    # verify session_name
    if not 'session_name' in sconf:
        raise exc.ConfigError('config requires "session_name"')

    if not 'windows' in sconf:
        raise exc.ConfigError('config requires list of "windows"')

    for window in sconf['windows']:
        if not 'window_name' in window:
            raise exc.ConfigError('config window is missing "window_name"')

        if not 'panes' in window:
            raise exc.ConfigError(
                'config window %s requires list of panes' % window['window_name'])

    return True


def is_config_file(filename, extensions=['.yml', '.yaml', '.json', '.ini']):
    '''Is config compatible extension.

    :param filename: filename to check (e.g. ``mysession.json``).
    :type filename: string
    :param extensions: filetypes to check (e.g. ``['.yaml', '.json']``).
    :type extensions: list or string
    :rtype: bool
    '''

    extensions = [extensions] if isinstance(extensions, basestring) else extensions
    return any(filename.endswith(e) for e in extensions)


def in_dir(config_dir=os.path.expanduser('~/.tmuxp'), extensions=['.yml', '.yaml', '.json', '.ini']):
    '''Find configs in config_dir and current dir

    :param config_dir: directory to search
    :type config_dir: string
    :param extensions: filetypes to check (e.g. ``['.yaml', '.json']``).
    :type extensions: list
    :rtype: list
    '''
    configs = []

    for filename in os.listdir(config_dir):
        if is_config_file(filename, extensions) and not filename.startswith('.'):
            configs.append(filename)

    return configs


def in_cwd():
    '''Return list of configs in current working directory.

    If filename is ``.tmuxp.py``, ``.tmuxp.json``, ``.tmuxp.yaml`` or
    ``.tmuxp.ini``.

    :rtype: list
    '''
    configs = []

    for filename in os.listdir(os.getcwd()):
        if filename.startswith('.tmuxp') and is_config_file(filename):
            configs.append(filename)

    return configs


def inline(config):
    '''Opposite of :meth:`config.expand`. Where possible, inline.

    :param config: unexpanded config file
    :type config: dict
    :rtype: dict
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
    :rtype: dict
    '''

    '''any config section, session, window, pane that can
    contain the 'shell_command' value
    '''
    if ('shell_command' in config and isinstance(config['shell_command'], basestring)):
        config['shell_command'] = [config['shell_command']]
    elif not 'windows' in config and not 'panes' in config and isinstance(config, basestring):
        config = {'shell_command': [config]}

    if ('shell_command_before' in config and isinstance(config['shell_command_before'], basestring)):
        config['shell_command_before'] = [config['shell_command_before']]

    # recurse into window and pane config items
    if 'windows' in config:
        config['windows'] = [
            expand(window) for window in config['windows']
        ]
    elif 'panes' in config:
        for p in config['panes']:
            if isinstance(p, basestring):
                p_index = config['panes'].index(p)
                config['panes'][p_index] = {
                    'shell_command': [p]
                }
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
    :rtype: dict
    '''

    '''
    prepends a pane's ``shell_command`` list with the window and sessions'
    ``shell_command_before``.
    '''

    session_start_directory = config['start_directory'] if 'start_directory' in config else None

    for windowconfig in config['windows']:
        if not 'start_directory' in windowconfig and session_start_directory:
            windowconfig['start_directory'] = session_start_directory
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


def import_tmuxinator(sconf):
    '''Import yaml configs from `tmuxinator`_.

    .. _tmuxinator: https://github.com/aziz/tmuxinator

    :todo: handle 'root' with a cd shell_command_before

    :param sconf: python dict for session configuration
    :type sconf: dict
    '''

    tmuxp_config = {}

    if 'project_name' in sconf:
        tmuxp_config['session_name'] = sconf['project_name']
    elif 'name' in sconf:
        tmuxp_config['session_name'] = sconf['name']
    else:
        tmuxp_config['session_name'] = None

    if 'cli_args' in sconf:
        tmuxp_config['config'] = sconf['cli_args']

        if '-f' in tmuxp_config['config']:
            tmuxp_config['config'] = tmuxp_config[
                'config'].replace('-f', '').strip()
    elif 'tmux_options' in sconf:
        tmuxp_config['config'] = sconf['tmux_options']

        if '-f' in tmuxp_config['config']:
            tmuxp_config['config'] = tmuxp_config[
                'config'].replace('-f', '').strip()

    if 'socket_name' in sconf:
        tmuxp_config['socket_name'] = sconf['socket_name']

    tmuxp_config['windows'] = []

    if 'tabs' in sconf:
        sconf['windows'] = sconf.pop('tabs')

    if 'pre' in sconf and 'pre_window' in sconf:
        tmuxp_config['shell_command'] = sconf['pre']

        if isinstance(sconf['pre'], basestring):
            tmuxp_config['shell_command_before'] = [sconf['pre_window']]
        else:
            tmuxp_config['shell_command_before'] = sconf['pre_window']
    elif 'pre' in sconf:
        if isinstance(sconf['pre'], basestring):
            tmuxp_config['shell_command_before'] = [sconf['pre']]
        else:
            tmuxp_config['shell_command_before'] = sconf['pre']

    if 'rbenv' in sconf:
        if 'shell_command_before' not in tmuxp_config:
            tmuxp_config['shell_command_before'] = []
        tmuxp_config['shell_command_before'].append(
            'rbenv shell %s' % sconf['rbenv']
        )

    for w in sconf['windows']:
        for k, v in w.items():

            windowdict = {}

            windowdict['window_name'] = k

            if isinstance(v, basestring) or v is None:
                windowdict['panes'] = [v]
                tmuxp_config['windows'].append(windowdict)
                continue
            elif isinstance(v, list):
                windowdict['panes'] = v
                tmuxp_config['windows'].append(windowdict)
                continue

            if 'pre' in v:
                windowdict['shell_command_before'] = v['pre']
            if 'panes' in v:
                windowdict['panes'] = v['panes']

            if 'layout' in v:
                windowdict['layout'] = v['layout']
            tmuxp_config['windows'].append(windowdict)

    return tmuxp_config


def import_teamocil(sconf):
    '''Import yaml configs from `teamocil`_.

    .. _teamocil: https://github.com/remiprev/teamocil

    :todo: change  'root' to a cd or start_directory
    :todo: width in pane -> main-pain-width
    :todo: with_env_var
    :todo: clear
    :todo: cmd_separator

    :param sconf: python dict for session configuration
    :type sconf: dict
    '''

    tmuxp_config = {}

    if 'session' in sconf:
        sconf = sconf['session']

    if 'name' in sconf:
        tmuxp_config['session_name'] = sconf['name']
    else:
        tmuxp_config['session_name'] = None

    tmuxp_config['windows'] = []

    for w in sconf['windows']:

        windowdict = {}

        windowdict['window_name'] = w['name']
        if 'clear' in w:
            windowdict['clear'] = w['clear']

        if 'filters' in w:
            if 'before' in w['filters']:
                for b in w['filters']['before']:
                    windowdict['shell_command_before'] = w['filters']['before']
            if 'after' in w['filters']:
                for b in w['filters']['after']:
                    windowdict['shell_command_after'] = w['filters']['after']

        if 'splits' in w:
            w['panes'] = w.pop('splits')

        if 'panes' in w:
            for p in w['panes']:
                if 'cmd' in p:
                    p['shell_command'] = p.pop('cmd')
                if 'width' in p:
                    # todo support for height/width
                    p.pop('width')
            windowdict['panes'] = w['panes']

        if 'layout' in w:
            windowdict['layout'] = w['layout']
        tmuxp_config['windows'].append(windowdict)

    return tmuxp_config

