# -*- coding: utf-8 -*-
"""Test for tmuxp command line interface."""

from __future__ import absolute_import, print_function, with_statement

import os

import libtmux
import pytest
from click.testing import CliRunner

from tmuxp import cli, config
from tmuxp.cli import is_pure_name, load_workspace, resolve_config_path

from .fixtures._util import curjoin


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


def test_resolve_dot(tmpdir, monkeypatch):
    homedir = tmpdir.join('home').mkdir()
    monkeypatch.setenv('HOME', homedir)
    configdir = homedir.join('.tmuxp').mkdir()

    user_config_name = 'myconfig'
    user_config = configdir.join('%s.yaml' % user_config_name).ensure()

    projectdir = homedir.join('work').join('project')
    projectdir.join('.tmuxp.yaml').ensure()
    project_config = str(projectdir.join('.tmuxp.yaml'))

    with projectdir.as_cwd():
        expect = project_config
        assert resolve_config_path('.') == expect
        assert resolve_config_path('./') == expect
        assert resolve_config_path('') == expect
        assert resolve_config_path('../project') == expect
        assert resolve_config_path('../project/') == expect
        assert resolve_config_path('.tmuxp.yaml') == expect
        assert resolve_config_path(
            '../../.tmuxp/%s.yaml' % user_config_name) == str(user_config)
        assert resolve_config_path('myconfig') == str(user_config)
        assert resolve_config_path(
            '~/.tmuxp/myconfig.yaml') == str(user_config)

        with pytest.raises(Exception):
            resolve_config_path('.tmuxp.json')
        with pytest.raises(Exception):
            resolve_config_path('.tmuxp.ini')
        with pytest.raises(Exception):
            resolve_config_path('../')
        with pytest.raises(Exception):
            resolve_config_path('mooooooo')

    with homedir.as_cwd():
        expect = project_config
        assert resolve_config_path('work/project') == expect
        assert resolve_config_path('work/project/') == expect
        assert resolve_config_path('./work/project') == expect
        assert resolve_config_path('./work/project/') == expect
        assert resolve_config_path(
            '.tmuxp/%s.yaml' % user_config_name) == str(user_config)
        assert resolve_config_path(
            './.tmuxp/%s.yaml' % user_config_name) == str(user_config)
        assert resolve_config_path('myconfig') == str(user_config)
        assert resolve_config_path(
            '~/.tmuxp/myconfig.yaml') == str(user_config)

        with pytest.raises(Exception):
            resolve_config_path('')
        with pytest.raises(Exception):
            resolve_config_path('.')
        with pytest.raises(Exception):
            resolve_config_path('.tmuxp.yaml')
        with pytest.raises(Exception):
            resolve_config_path('../')
        with pytest.raises(Exception):
            resolve_config_path('mooooooo')

    with configdir.as_cwd():
        expect = project_config
        assert resolve_config_path('../work/project') == expect
        assert resolve_config_path('../../home/work/project') == expect
        assert resolve_config_path('../work/project/') == expect
        assert resolve_config_path(
            '%s.yaml' % user_config_name) == str(user_config)
        assert resolve_config_path(
            './%s.yaml' % user_config_name) == str(user_config)
        assert resolve_config_path('myconfig') == str(user_config)
        assert resolve_config_path(
            '~/.tmuxp/myconfig.yaml') == str(user_config)

        with pytest.raises(Exception):
            resolve_config_path('')
        with pytest.raises(Exception):
            resolve_config_path('.')
        with pytest.raises(Exception):
            resolve_config_path('.tmuxp.yaml')
        with pytest.raises(Exception):
            resolve_config_path('../')
        with pytest.raises(Exception):
            resolve_config_path('mooooooo')

    with tmpdir.as_cwd():
        expect = project_config
        assert resolve_config_path('home/work/project') == expect
        assert resolve_config_path('./home/work/project/') == expect
        assert resolve_config_path(
            'home/.tmuxp/%s.yaml' % user_config_name) == str(user_config)
        assert resolve_config_path(
            './home/.tmuxp/%s.yaml' % user_config_name) == str(user_config)
        assert resolve_config_path('myconfig') == str(user_config)
        assert resolve_config_path(
            '~/.tmuxp/myconfig.yaml') == str(user_config)

        with pytest.raises(Exception):
            resolve_config_path('')
        with pytest.raises(Exception):
            resolve_config_path('.')
        with pytest.raises(Exception):
            resolve_config_path('.tmuxp.yaml')
        with pytest.raises(Exception):
            resolve_config_path('../')
        with pytest.raises(Exception):
            resolve_config_path('mooooooo')


def test_load_workspace(server, monkeypatch):
    # this is an implementation test. Since this testsuite may be ran within
    # a tmux session by the developer themselv, delete the TMUX variable
    # temporarily.
    monkeypatch.delenv('TMUX')
    session_file = curjoin("workspacebuilder/two_pane.yaml")

    # open it detached
    session = load_workspace(
        session_file, socket_name=server.socket_name,
        detached=True
    )

    assert isinstance(session, libtmux.Session)
    assert session.name == 'sampleconfig'


def test_zsh_autotitle_warning(monkeypatch):
    runner = CliRunner()

    monkeypatch.delenv('DISABLE_AUTO_TITLE')
    monkeypatch.setenv('SHELL', 'zsh')
    result = runner.invoke(cli.cli, ['load'])
    assert 'Please set' in result.output

    monkeypatch.setenv('DISABLE_AUTO_TITLE', 'true')
    result = runner.invoke(cli.cli, ['load'])
    assert 'Please set' not in result.output

    monkeypatch.delenv('DISABLE_AUTO_TITLE')
    monkeypatch.setenv('SHELL', 'sh')
    result = runner.invoke(cli.cli, ['load'])
    assert 'Please set' not in result.output
