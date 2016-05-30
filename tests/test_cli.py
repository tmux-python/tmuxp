# -*- coding: utf-8 -*-
"""Test for tmuxp command line interface."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals, with_statement)

import os
import pytest

from tmuxp import cli, config
from tmuxp.cli import resolve_config_path, is_pure_name


def test_creates_config_dir_not_exists(tmpdir):
    """cli.startup() creates config dir if not exists."""

    cli.startup(str(tmpdir))
    assert os.path.exists(str(tmpdir))


def test_in_dir_from_config_dir(tmpdir):
    """config.in_dir() finds configs config dir."""

    cli.startup(str(tmpdir))
    tmpdir.join("myconfig.yaml").write("")
    tmpdir.join("myconfig.json").write("")
    configs_found = config.in_dir(str(tmpdir))

    assert len(configs_found) == 2


def test_ignore_non_configs_from_current_dir(tmpdir):
    """cli.in_dir() ignore non-config from config dir."""

    cli.startup(str(tmpdir))

    tmpdir.join("myconfig.psd").write("")
    tmpdir.join("watmyconfig.json").write("")
    configs_found = config.in_dir(str(tmpdir))
    assert len(configs_found) == 1


def test_get_configs_cwd(tmpdir):
    """config.in_cwd() find config in shell current working directory."""

    confdir = tmpdir.mkdir("tmuxpconf2")
    with confdir.as_cwd():
        config1 = open('.tmuxp.json', 'w+b')
        config1.close()

        configs_found = config.in_cwd()
        assert len(configs_found) == 1
        assert '.tmuxp.json' in configs_found


@pytest.mark.parametrize('path,expect', [
    ('.', False),
    ('./', False),
    ('', False),
    ('.tmuxp.yaml', False),
    ('../.tmuxp.yaml', False),
    ('../', False),
    ('/hello/world', False),
    ('~/.tmuxp/hey', False),
    ('~/work/c/tmux/', False),
    ('~/work/c/tmux/.tmuxp.yaml', False),
    ('myproject', True),
])
def test_is_pure_name(path, expect):
    assert is_pure_name(path) == expect

"""
    scans for .tmuxp.{yaml,yml,json} in directory, returns first result
    log warning if multiple found:

    - current directory: ., ./, noarg
    - relative to cwd directory: ../, ./hello/, hello/, ./hello/
    - absolute directory: /path/to/dir, /path/to/dir/, ~/
    - no path, no ext, config_dir: projectname, tmuxp

    load file directly -

    - no directory (cwd): .tmuxp.yaml
    - relative to cwd: ../.tmuxp.yaml, ./hello/.tmuxp.yaml
    - absolute path: /path/to/file.yaml, ~/path/to/file/.tmuxp.yaml

    Any case where file is not found should return error.
"""


def test_resolve_dot(tmpdir):
    homedir = tmpdir.join('home').mkdir()
    configdir = homedir.join('.tmuxp').mkdir()

    userconfig_name = 'myconfig'
    configdir.join(userconfig_name).ensure()

    projectdir = homedir.join('work').join('project')
    projectdir.join('.tmuxp.yaml').ensure()

    with projectdir.as_cwd():
        pass
