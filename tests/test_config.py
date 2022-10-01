"""Test for tmuxp configuration import, inlining, expanding and export."""
import os
import pathlib
import types
import typing
from typing import Union

import pytest

from tmuxp import config, exc
from tmuxp.config_reader import ConfigReader

from .constants import EXAMPLE_PATH

if typing.TYPE_CHECKING:
    from .fixtures.structures import ConfigTestData


@pytest.fixture
def config_fixture():
    """Deferred import of tmuxp.tests.fixtures.*

    pytest setup (conftest.py) patches os.environ["HOME"], delay execution of
    os.path.expanduser until here.
    """
    from .fixtures import config as test_config_data
    from .fixtures.structures import ConfigTestData

    return ConfigTestData(
        **{
            k: v
            for k, v in test_config_data.__dict__.items()
            if isinstance(v, types.ModuleType)
        }
    )


def load_yaml(path: Union[str, pathlib.Path]) -> str:
    return ConfigReader._from_file(
        pathlib.Path(path) if isinstance(path, str) else path
    )


def load_config(path: Union[str, pathlib.Path]) -> str:
    return ConfigReader._from_file(
        pathlib.Path(path) if isinstance(path, str) else path
    )


def test_export_json(tmp_path: pathlib.Path, config_fixture: "ConfigTestData"):
    json_config_file = tmp_path / "config.json"

    configparser = ConfigReader(config_fixture.sampleconfig.sampleconfigdict)

    json_config_data = configparser.dump("json", indent=2)

    json_config_file.write_text(json_config_data, encoding="utf-8")

    new_config_data = ConfigReader._from_file(path=json_config_file)
    assert config_fixture.sampleconfig.sampleconfigdict == new_config_data


def test_export_yaml(tmp_path: pathlib.Path, config_fixture: "ConfigTestData"):
    yaml_config_file = tmp_path / "config.yaml"

    sampleconfig = config.inline(config_fixture.sampleconfig.sampleconfigdict)
    configparser = ConfigReader(sampleconfig)

    yaml_config_data = configparser.dump("yaml", indent=2, default_flow_style=False)

    yaml_config_file.write_text(yaml_config_data, encoding="utf-8")

    new_config_data = load_config(str(yaml_config_file))
    assert config_fixture.sampleconfig.sampleconfigdict == new_config_data


def test_scan_config(tmp_path: pathlib.Path):
    configs = []

    garbage_file = tmp_path / "config.psd"
    garbage_file.write_text("wat", encoding="utf-8")

    for r, d, f in os.walk(str(tmp_path)):
        for filela in (x for x in f if x.endswith((".json", ".ini", "yaml"))):
            configs.append(str(tmp_path / filela))

    files = 0
    config_json = tmp_path / "config.json"
    config_yaml = tmp_path / "config.yaml"
    config_ini = tmp_path / "config.ini"
    if config_json.exists():
        files += 1
        assert str(config_json) in configs

    if config_yaml.exists():
        files += 1
        assert str(config_yaml) in configs

    if config_ini.exists():
        files += 1
        assert str(config_ini) in configs

    assert len(configs) == files


def test_config_expand1(config_fixture: "ConfigTestData"):
    """Expand shell commands from string to list."""
    test_config = config.expand(config_fixture.expand1.before_config)
    assert test_config == config_fixture.expand1.after_config()


def test_config_expand2(config_fixture: "ConfigTestData"):
    """Expand shell commands from string to list."""
    unexpanded_dict = ConfigReader._load(
        format="yaml", content=config_fixture.expand2.unexpanded_yaml()
    )
    expanded_dict = ConfigReader._load(
        format="yaml", content=config_fixture.expand2.expanded_yaml()
    )
    assert config.expand(unexpanded_dict) == expanded_dict


"""Tests for :meth:`config.inline()`."""

ibefore_config = {  # inline config
    "session_name": "sampleconfig",
    "start_directory": "~",
    "windows": [
        {
            "shell_command": ["top"],
            "window_name": "editor",
            "panes": [{"shell_command": ["vim"]}, {"shell_command": ['cowsay "hey"']}],
            "layout": "main-verticle",
        },
        {
            "window_name": "logging",
            "panes": [{"shell_command": ["tail -F /var/log/syslog"]}],
        },
        {"options": {"automatic-rename": True}, "panes": [{"shell_command": ["htop"]}]},
    ],
}

iafter_config = {
    "session_name": "sampleconfig",
    "start_directory": "~",
    "windows": [
        {
            "shell_command": "top",
            "window_name": "editor",
            "panes": ["vim", 'cowsay "hey"'],
            "layout": "main-verticle",
        },
        {"window_name": "logging", "panes": ["tail -F /var/log/syslog"]},
        {"options": {"automatic-rename": True}, "panes": ["htop"]},
    ],
}


def test_inline_config():
    """:meth:`config.inline()` shell commands list to string."""

    test_config = config.inline(ibefore_config)
    assert test_config == iafter_config


"""Test config inheritance for the nested 'start_command'."""

inheritance_config_before = {
    "session_name": "sampleconfig",
    "start_directory": "/",
    "windows": [
        {
            "window_name": "editor",
            "start_directory": "~",
            "panes": [{"shell_command": ["vim"]}, {"shell_command": ['cowsay "hey"']}],
            "layout": "main-verticle",
        },
        {
            "window_name": "logging",
            "panes": [{"shell_command": ["tail -F /var/log/syslog"]}],
        },
        {"window_name": "shufu", "panes": [{"shell_command": ["htop"]}]},
        {"options": {"automatic-rename": True}, "panes": [{"shell_command": ["htop"]}]},
    ],
}

inheritance_config_after = {
    "session_name": "sampleconfig",
    "start_directory": "/",
    "windows": [
        {
            "window_name": "editor",
            "start_directory": "~",
            "panes": [{"shell_command": ["vim"]}, {"shell_command": ['cowsay "hey"']}],
            "layout": "main-verticle",
        },
        {
            "window_name": "logging",
            "panes": [{"shell_command": ["tail -F /var/log/syslog"]}],
        },
        {"window_name": "shufu", "panes": [{"shell_command": ["htop"]}]},
        {"options": {"automatic-rename": True}, "panes": [{"shell_command": ["htop"]}]},
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


def test_shell_command_before(config_fixture: "ConfigTestData"):
    """Config inheritance for the nested 'start_command'."""
    test_config = config_fixture.shell_command_before.config_unexpanded
    test_config = config.expand(test_config)

    assert test_config == config_fixture.shell_command_before.config_expanded()

    test_config = config.trickle(test_config)
    assert test_config == config_fixture.shell_command_before.config_after()


def test_in_session_scope(config_fixture: "ConfigTestData"):
    sconfig = ConfigReader._load(
        format="yaml", content=config_fixture.shell_command_before_session.before
    )

    config.validate_schema(sconfig)

    assert config.expand(sconfig) == sconfig
    assert config.expand(config.trickle(sconfig)) == ConfigReader._load(
        format="yaml", content=config_fixture.shell_command_before_session.expected
    )


def test_trickle_relative_start_directory(config_fixture: "ConfigTestData"):
    test_config = config.trickle(config_fixture.trickle.before)
    assert test_config == config_fixture.trickle.expected


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
    sconfig = ConfigReader._load(format="yaml", content=test_yaml)
    config.validate_schema(sconfig)

    assert config.expand(config.trickle(sconfig))["windows"][1]["panes"][0] == {
        "shell_command": []
    }


def test_expands_blank_panes(config_fixture: "ConfigTestData"):
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
    yaml_config_file = EXAMPLE_PATH / "blank-panes.yaml"
    test_config = load_config(yaml_config_file)
    assert config.expand(test_config) == config_fixture.expand_blank.expected


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

    sconfig = ConfigReader._load(format="yaml", content=yaml_config)

    with pytest.raises(exc.ConfigError) as excinfo:
        config.validate_schema(sconfig)
        assert excinfo.matches(r'requires "session_name"')


def test_no_windows():
    yaml_config = """
    session_name: test session
    """

    sconfig = ConfigReader._load(format="yaml", content=yaml_config)

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

    sconfig = ConfigReader._load(format="yaml", content=yaml_config)

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

    sconfig = ConfigReader._load(format="yaml", content=yaml_config)

    monkeypatch.setenv(str(env_key), str(env_val))
    sconfig = config.expand(sconfig)
    assert "%s/test" % env_val == sconfig["start_directory"]
    assert (
        "%s/test2" % env_val
        in sconfig["shell_command_before"]["shell_command"][0]["cmd"]
    )
    assert "%s/test3" % env_val == sconfig["before_script"]
    assert "hi - %s" % env_val == sconfig["session_name"]
    assert "%s/moo" % env_val == sconfig["global_options"]["default-shell"]
    assert "%s/lol" % env_val == sconfig["options"]["default-command"]
    assert "logging @ %s" % env_val == sconfig["windows"][1]["window_name"]


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

    sconfig = ConfigReader._load(format="yaml", content=yaml_config)

    with pytest.raises(exc.ConfigError) as excinfo:
        config.validate_schema(sconfig)
        assert excinfo.matches("only supports list type")
