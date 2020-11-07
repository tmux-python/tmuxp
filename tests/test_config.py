# -*- coding: utf-8 -*-
"""Test for tmuxp configuration import, inlining, expanding and export."""

from __future__ import absolute_import, unicode_literals

import os

import pytest

import kaptan

from tmuxp import config, exc

from . import example_dir
from .fixtures import config as fixtures

TMUXP_DIR = os.path.join(os.path.dirname(__file__), '.tmuxp')


def load_yaml(yaml):
    return kaptan.Kaptan(handler='yaml').import_config(yaml).get()


def load_config(_file):
    return kaptan.Kaptan().import_config(_file).get()


def test_export_json(tmpdir):
    json_config_file = tmpdir.join('config.json')

    configparser = kaptan.Kaptan()
    configparser.import_config(fixtures.sampleconfig.sampleconfigdict)

    json_config_data = configparser.export('json', indent=2)

    json_config_file.write(json_config_data)

    new_config = kaptan.Kaptan()
    new_config_data = new_config.import_config(str(json_config_file)).get()
    assert fixtures.sampleconfig.sampleconfigdict == new_config_data


def test_export_yaml(tmpdir):
    yaml_config_file = tmpdir.join('config.yaml')

    configparser = kaptan.Kaptan()
    sampleconfig = config.inline(fixtures.sampleconfig.sampleconfigdict)
    configparser.import_config(sampleconfig)

    yaml_config_data = configparser.export('yaml', indent=2, default_flow_style=False)

    yaml_config_file.write(yaml_config_data)

    new_config_data = load_config(str(yaml_config_file))
    assert fixtures.sampleconfig.sampleconfigdict == new_config_data


def test_scan_config(tmpdir):
    configs = []

    garbage_file = tmpdir.join('config.psd')
    garbage_file.write('wat')

    for r, d, f in os.walk(str(tmpdir)):
        for filela in (x for x in f if x.endswith(('.json', '.ini', 'yaml'))):
            configs.append(str(tmpdir.join(filela)))

    files = 0
    if tmpdir.join('config.json').check():
        files += 1
        assert str(tmpdir.join('config.json')) in configs

    if tmpdir.join('config.yaml').check():
        files += 1
        assert str(tmpdir.join('config.yaml')) in configs

    if tmpdir.join('config.ini').check():
        files += 1
        assert str(tmpdir.join('config.ini')) in configs

    assert len(configs) == files


def test_config_expand1():
    """Expand shell commands from string to list."""
    test_config = config.expand(fixtures.expand1.before_config)
    assert test_config == fixtures.expand1.after_config


def test_config_expand2():
    """Expand shell commands from string to list."""

    unexpanded_dict = load_yaml(fixtures.expand2.unexpanded_yaml)

    expanded_dict = load_yaml(fixtures.expand2.expanded_yaml)

    assert config.expand(unexpanded_dict) == expanded_dict


"""Tests for :meth:`config.inline()`."""

ibefore_config = {  # inline config
    'session_name': 'sampleconfig',
    'start_directory': '~',
    'windows': [
        {
            'shell_command': ['top'],
            'window_name': 'editor',
            'panes': [{'shell_command': ['vim']}, {'shell_command': ['cowsay "hey"']}],
            'layout': 'main-verticle',
        },
        {
            'window_name': 'logging',
            'panes': [{'shell_command': ['tail -F /var/log/syslog']}],
        },
        {'options': {'automatic-rename': True}, 'panes': [{'shell_command': ['htop']}]},
    ],
}

iafter_config = {
    'session_name': 'sampleconfig',
    'start_directory': '~',
    'windows': [
        {
            'shell_command': 'top',
            'window_name': 'editor',
            'panes': ['vim', 'cowsay "hey"'],
            'layout': 'main-verticle',
        },
        {'window_name': 'logging', 'panes': ['tail -F /var/log/syslog']},
        {'options': {'automatic-rename': True}, 'panes': ['htop']},
    ],
}


def test_inline_config():
    """:meth:`config.inline()` shell commands list to string."""

    test_config = config.inline(ibefore_config)
    assert test_config == iafter_config


"""Test config inheritance for the nested 'start_command'."""

inheritance_config_before = {
    'session_name': 'sampleconfig',
    'start_directory': '/',
    'windows': [
        {
            'window_name': 'editor',
            'start_directory': '~',
            'panes': [{'shell_command': ['vim']}, {'shell_command': ['cowsay "hey"']}],
            'layout': 'main-verticle',
        },
        {
            'window_name': 'logging',
            'panes': [{'shell_command': ['tail -F /var/log/syslog']}],
        },
        {'window_name': 'shufu', 'panes': [{'shell_command': ['htop']}]},
        {'options': {'automatic-rename': True}, 'panes': [{'shell_command': ['htop']}]},
    ],
}

inheritance_config_after = {
    'session_name': 'sampleconfig',
    'start_directory': '/',
    'windows': [
        {
            'window_name': 'editor',
            'start_directory': '~',
            'panes': [{'shell_command': ['vim']}, {'shell_command': ['cowsay "hey"']}],
            'layout': 'main-verticle',
        },
        {
            'window_name': 'logging',
            'panes': [{'shell_command': ['tail -F /var/log/syslog']}],
        },
        {'window_name': 'shufu', 'panes': [{'shell_command': ['htop']}]},
        {'options': {'automatic-rename': True}, 'panes': [{'shell_command': ['htop']}]},
    ],
}


def test_inheritance_config():
    config = inheritance_config_before

    # TODO: Look at verifying window_start_directory
    # if 'start_directory' in config:
    #     session_start_directory = config['start_directory']
    # else:
    #     session_start_directory = None

    # for windowconfitem in config['windows']:
    #     window_start_directory = None
    #
    #     if 'start_directory' in windowconfitem:
    #         window_start_directory = windowconfitem['start_directory']
    #     elif session_start_directory:
    #         window_start_directory = session_start_directory
    #
    #     for paneconfitem in windowconfitem['panes']:
    #         if 'start_directory' in paneconfitem:
    #             pane_start_directory = paneconfitem['start_directory']
    #         elif window_start_directory:
    #             paneconfitem['start_directory'] = window_start_directory
    #         elif session_start_directory:
    #             paneconfitem['start_directory'] = session_start_directory

    assert config == inheritance_config_after


def test_shell_command_before():
    """Config inheritance for the nested 'start_command'."""
    test_config = fixtures.shell_command_before.config_unexpanded
    test_config = config.expand(test_config)

    assert test_config == fixtures.shell_command_before.config_expanded

    test_config = config.trickle(test_config)
    assert test_config == fixtures.shell_command_before.config_after


def test_in_session_scope():
    sconfig = load_yaml(fixtures.shell_command_before_session.before)

    config.validate_schema(sconfig)

    assert config.expand(sconfig) == sconfig
    assert config.expand(config.trickle(sconfig)) == load_yaml(
        fixtures.shell_command_before_session.expected
    )


def test_trickle_relative_start_directory():
    test_config = config.trickle(fixtures.trickle.before)
    assert test_config == fixtures.trickle.expected


def test_trickle_window_with_no_pane_config():
    test_yaml = """
    session_name: test_session
    windows:
    - window_name: test_1
      panes:
      - shell_command:
        - ls -l
    - window_name: test_no_panes
    """
    sconfig = load_yaml(test_yaml)
    config.validate_schema(sconfig)

    assert config.expand(config.trickle(sconfig))['windows'][1]['panes'][0] == {
        'shell_command': []
    }


def test_expands_blank_panes():
    """Expand blank config into full form.

    Handle ``NoneType`` and 'blank'::

    # nothing, None, 'blank'
    'panes': [
        None,
        'blank'
    ]

    # should be blank
    'panes': [
        'shell_command': []
    ]

    Blank strings::

        panes: [
            ''
        ]

        # should output to:
        panes:
            'shell_command': ['']

    """

    yaml_config_file = os.path.join(example_dir, 'blank-panes.yaml')
    test_config = load_config(yaml_config_file)
    assert config.expand(test_config) == fixtures.expand_blank.expected


def test_no_session_name():
    yaml_config = """
    - window_name: editor
      panes:
      shell_command:
      - tail -F /var/log/syslog
      start_directory: /var/log
    - window_name: logging
      automatic-rename: true
      panes:
      - shell_command:
      - htop
    """

    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(yaml_config).get()

    with pytest.raises(exc.ConfigError) as excinfo:
        config.validate_schema(sconfig)
        assert excinfo.matches(r'requires "session_name"')


def test_no_windows():
    yaml_config = """
    session_name: test session
    """

    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(yaml_config).get()

    with pytest.raises(exc.ConfigError) as excinfo:
        config.validate_schema(sconfig)
        assert excinfo.match(r'list of "windows"')


def test_no_window_name():
    yaml_config = """
    session_name: test session
    windows:
    - window_name: editor
      panes:
      shell_command:
      - tail -F /var/log/syslog
      start_directory: /var/log
    - automatic-rename: true
      panes:
      - shell_command:
      - htop
    """

    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(yaml_config).get()

    with pytest.raises(exc.ConfigError) as excinfo:
        config.validate_schema(sconfig)
        assert excinfo.matches('missing "window_name"')


def test_replaces_env_variables(monkeypatch):
    env_key = "TESTHEY92"
    env_val = "HEYO1"
    yaml_config = """
    start_directory: {TEST_VAR}/test
    shell_command_before: {TEST_VAR}/test2
    before_script: {TEST_VAR}/test3
    session_name: hi - {TEST_VAR}
    options:
        default-command: {TEST_VAR}/lol
    global_options:
        default-shell: {TEST_VAR}/moo
    windows:
    - window_name: editor
      panes:
      - shell_command:
      - tail -F /var/log/syslog
      start_directory: /var/log
    - window_name: logging @ {TEST_VAR}
      automatic-rename: true
      panes:
      - shell_command:
      - htop
    """.format(
        TEST_VAR="${%s}" % env_key
    )

    sconfig = load_yaml(yaml_config)

    monkeypatch.setenv(str(env_key), str(env_val))
    sconfig = config.expand(sconfig)
    assert "%s/test" % env_val == sconfig['start_directory']
    assert "%s/test2" % env_val in sconfig['shell_command_before']
    assert "%s/test3" % env_val == sconfig['before_script']
    assert "hi - %s" % env_val == sconfig['session_name']
    assert "%s/moo" % env_val == sconfig['global_options']['default-shell']
    assert "%s/lol" % env_val == sconfig['options']['default-command']
    assert "logging @ %s" % env_val == sconfig['windows'][1]['window_name']


def test_plugins():
    yaml_config = """
    session_name: test session
    plugins: tmuxp-plugin-one.plugin.TestPluginOne
    windows:
    - window_name: editor
      panes:
      shell_command:
      - tail -F /var/log/syslog
      start_directory: /var/log
    """

    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(yaml_config).get()

    with pytest.raises(exc.ConfigError) as excinfo:
        config.validate_schema(sconfig)
        assert excinfo.matches('only supports list type')
