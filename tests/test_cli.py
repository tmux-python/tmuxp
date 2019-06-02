# -*- coding: utf-8 -*-
"""Test for tmuxp command line interface."""
from __future__ import absolute_import

import json
import os

import pytest

import click
from click.testing import CliRunner

import libtmux
from libtmux.common import has_lt_version
from tmuxp import cli, config
from tmuxp.cli import get_config_dir, is_pure_name, load_workspace, scan_config

from .fixtures._util import curjoin, loadfixture


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


@pytest.mark.parametrize(
    'path,expect',
    [
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
    ],
)
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


@pytest.fixture
def homedir(tmpdir):
    return tmpdir.join('home').mkdir()


@pytest.fixture
def configdir(homedir):
    return homedir.join('.tmuxp').mkdir()


@pytest.fixture
def projectdir(homedir):
    return homedir.join('work').join('project')


def test_tmuxp_configdir_env_var(tmpdir, monkeypatch):
    monkeypatch.setenv('TMUXP_CONFIGDIR', str(tmpdir))

    assert get_config_dir() == tmpdir


def test_tmuxp_configdir_xdg_config_dir(tmpdir, monkeypatch):
    monkeypatch.setenv('XDG_CONFIG_HOME', str(tmpdir))
    tmux_dir = tmpdir.mkdir("tmuxp")

    assert get_config_dir() == str(tmux_dir)


def test_resolve_dot(tmpdir, homedir, configdir, projectdir, monkeypatch):
    monkeypatch.setenv('HOME', str(homedir))
    projectdir.join('.tmuxp.yaml').ensure()
    user_config_name = 'myconfig'
    user_config = configdir.join('%s.yaml' % user_config_name).ensure()

    project_config = str(projectdir.join('.tmuxp.yaml'))

    with projectdir.as_cwd():
        expect = project_config
        assert scan_config('.') == expect
        assert scan_config('./') == expect
        assert scan_config('') == expect
        assert scan_config('../project') == expect
        assert scan_config('../project/') == expect
        assert scan_config('.tmuxp.yaml') == expect
        assert scan_config('../../.tmuxp/%s.yaml' % user_config_name) == str(
            user_config
        )
        assert scan_config('myconfig') == str(user_config)
        assert scan_config('~/.tmuxp/myconfig.yaml') == str(user_config)

        with pytest.raises(Exception):
            scan_config('.tmuxp.json')
        with pytest.raises(Exception):
            scan_config('.tmuxp.ini')
        with pytest.raises(Exception):
            scan_config('../')
        with pytest.raises(Exception):
            scan_config('mooooooo')

    with homedir.as_cwd():
        expect = project_config
        assert scan_config('work/project') == expect
        assert scan_config('work/project/') == expect
        assert scan_config('./work/project') == expect
        assert scan_config('./work/project/') == expect
        assert scan_config('.tmuxp/%s.yaml' % user_config_name) == str(user_config)
        assert scan_config('./.tmuxp/%s.yaml' % user_config_name) == str(user_config)
        assert scan_config('myconfig') == str(user_config)
        assert scan_config('~/.tmuxp/myconfig.yaml') == str(user_config)

        with pytest.raises(Exception):
            scan_config('')
        with pytest.raises(Exception):
            scan_config('.')
        with pytest.raises(Exception):
            scan_config('.tmuxp.yaml')
        with pytest.raises(Exception):
            scan_config('../')
        with pytest.raises(Exception):
            scan_config('mooooooo')

    with configdir.as_cwd():
        expect = project_config
        assert scan_config('../work/project') == expect
        assert scan_config('../../home/work/project') == expect
        assert scan_config('../work/project/') == expect
        assert scan_config('%s.yaml' % user_config_name) == str(user_config)
        assert scan_config('./%s.yaml' % user_config_name) == str(user_config)
        assert scan_config('myconfig') == str(user_config)
        assert scan_config('~/.tmuxp/myconfig.yaml') == str(user_config)

        with pytest.raises(Exception):
            scan_config('')
        with pytest.raises(Exception):
            scan_config('.')
        with pytest.raises(Exception):
            scan_config('.tmuxp.yaml')
        with pytest.raises(Exception):
            scan_config('../')
        with pytest.raises(Exception):
            scan_config('mooooooo')

    with tmpdir.as_cwd():
        expect = project_config
        assert scan_config('home/work/project') == expect
        assert scan_config('./home/work/project/') == expect
        assert scan_config('home/.tmuxp/%s.yaml' % user_config_name) == str(user_config)
        assert scan_config('./home/.tmuxp/%s.yaml' % user_config_name) == str(
            user_config
        )
        assert scan_config('myconfig') == str(user_config)
        assert scan_config('~/.tmuxp/myconfig.yaml') == str(user_config)

        with pytest.raises(Exception):
            scan_config('')
        with pytest.raises(Exception):
            scan_config('.')
        with pytest.raises(Exception):
            scan_config('.tmuxp.yaml')
        with pytest.raises(Exception):
            scan_config('../')
        with pytest.raises(Exception):
            scan_config('mooooooo')


def test_scan_config_arg(homedir, configdir, projectdir, monkeypatch):
    runner = CliRunner()

    @click.command()
    @click.argument('config', type=cli.ConfigPath(exists=True), nargs=-1)
    def config_cmd(config):
        click.echo(config)

    monkeypatch.setenv('HOME', str(homedir))
    projectdir.join('.tmuxp.yaml').ensure()
    user_config_name = 'myconfig'
    user_config = configdir.join('%s.yaml' % user_config_name).ensure()

    project_config = str(projectdir.join('.tmuxp.yaml'))

    def check_cmd(config_arg):
        return runner.invoke(config_cmd, [config_arg]).output

    with projectdir.as_cwd():
        expect = project_config
        assert expect in check_cmd('.')
        assert expect in check_cmd('./')
        assert expect in check_cmd('')
        assert expect in check_cmd('../project')
        assert expect in check_cmd('../project/')
        assert expect in check_cmd('.tmuxp.yaml')
        assert str(user_config) in check_cmd('../../.tmuxp/%s.yaml' % user_config_name)
        assert user_config.purebasename in check_cmd('myconfig')
        assert str(user_config) in check_cmd('~/.tmuxp/myconfig.yaml')

        assert 'file not found' in check_cmd('.tmuxp.json')
        assert 'file not found' in check_cmd('.tmuxp.ini')
        assert 'No tmuxp files found' in check_cmd('../')
        assert 'config not found in config dir' in check_cmd('moo')


def test_load_workspace(server, monkeypatch):
    # this is an implementation test. Since this testsuite may be ran within
    # a tmux session by the developer himself, delete the TMUX variable
    # temporarily.
    monkeypatch.delenv('TMUX', raising=False)
    session_file = curjoin("workspacebuilder/two_pane.yaml")

    # open it detached
    session = load_workspace(
        session_file, socket_name=server.socket_name, detached=True
    )

    assert isinstance(session, libtmux.Session)
    assert session.name == 'sampleconfig'


@pytest.mark.skipif(
    has_lt_version('2.1'), reason='exact session name matches only tmux >= 2.1'
)
def test_load_workspace_name_match_regression_252(tmpdir, server, monkeypatch):
    monkeypatch.delenv('TMUX', raising=False)
    session_file = curjoin("workspacebuilder/two_pane.yaml")

    # open it detached
    session = load_workspace(
        session_file, socket_name=server.socket_name, detached=True
    )

    assert isinstance(session, libtmux.Session)
    assert session.name == 'sampleconfig'

    projfile = tmpdir.join('simple.yaml')

    projfile.write(
        """
session_name: sampleconfi
start_directory: './'
windows:
- panes:
    - echo 'hey'"""
    )

    # open it detached
    session = load_workspace(
        projfile.strpath, socket_name=server.socket_name, detached=True
    )
    assert session.name == 'sampleconfi'


def test_load_symlinked_workspace(server, tmpdir, monkeypatch):
    # this is an implementation test. Since this testsuite may be ran within
    # a tmux session by the developer himself, delete the TMUX variable
    # temporarily.
    monkeypatch.delenv('TMUX', raising=False)

    realtemp = tmpdir.mkdir('myrealtemp')
    linktemp = tmpdir.join('symlinktemp')
    linktemp.mksymlinkto(realtemp)
    projfile = linktemp.join('simple.yaml')

    projfile.write(
        """
session_name: samplesimple
start_directory: './'
windows:
- panes:
    - echo 'hey'"""
    )

    # open it detached
    session = load_workspace(
        projfile.strpath, socket_name=server.socket_name, detached=True
    )
    pane = session.attached_window.attached_pane

    assert isinstance(session, libtmux.Session)
    assert session.name == 'samplesimple'
    assert pane.current_path == realtemp.strpath


def test_regression_00132_session_name_with_dots(tmpdir, server, session):
    yaml_config = curjoin("workspacebuilder/regression_00132_dots.yaml")
    cli_args = [yaml_config]
    inputs = []
    runner = CliRunner()
    result = runner.invoke(
        cli.command_load, cli_args, input=''.join(inputs), standalone_mode=False
    )
    assert result.exception
    assert isinstance(result.exception, libtmux.exc.BadSessionName)


@pytest.mark.parametrize("cli_args", [(['load', '.']), (['load', '.tmuxp.yaml'])])
def test_load_zsh_autotitle_warning(cli_args, tmpdir, monkeypatch):
    # create dummy tmuxp yaml so we don't get yelled at
    tmpdir.join('.tmuxp.yaml').ensure()
    tmpdir.join('.oh-my-zsh').ensure(dir=True)
    monkeypatch.setenv('HOME', str(tmpdir))

    with tmpdir.as_cwd():
        runner = CliRunner()

        monkeypatch.delenv('DISABLE_AUTO_TITLE', raising=False)
        monkeypatch.setenv('SHELL', 'zsh')
        result = runner.invoke(cli.cli, cli_args)
        assert 'Please set' in result.output

        monkeypatch.setenv('DISABLE_AUTO_TITLE', 'false')
        result = runner.invoke(cli.cli, cli_args)
        assert 'Please set' in result.output

        monkeypatch.setenv('DISABLE_AUTO_TITLE', 'true')
        result = runner.invoke(cli.cli, cli_args)
        assert 'Please set' not in result.output

        monkeypatch.delenv('DISABLE_AUTO_TITLE', raising=False)
        monkeypatch.setenv('SHELL', 'sh')
        result = runner.invoke(cli.cli, cli_args)
        assert 'Please set' not in result.output


@pytest.mark.parametrize("cli_args", [(['convert', '.']), (['convert', '.tmuxp.yaml'])])
def test_convert(cli_args, tmpdir, monkeypatch):
    # create dummy tmuxp yaml so we don't get yelled at
    tmpdir.join('.tmuxp.yaml').write(
        """
session_name: hello
    """
    )
    tmpdir.join('.oh-my-zsh').ensure(dir=True)
    monkeypatch.setenv('HOME', str(tmpdir))

    with tmpdir.as_cwd():
        runner = CliRunner()

        runner.invoke(cli.cli, cli_args, input='y\ny\n')
        assert tmpdir.join('.tmuxp.json').check()
        assert tmpdir.join('.tmuxp.json').open().read() == json.dumps(
            {'session_name': 'hello'}, indent=2
        )


@pytest.mark.parametrize("cli_args", [(['import'])])
def test_import(cli_args, monkeypatch):
    runner = CliRunner()

    result = runner.invoke(cli.cli, cli_args)
    assert 'tmuxinator' in result.output
    assert 'teamocil' in result.output


@pytest.mark.parametrize(
    "cli_args,inputs",
    [
        (
            ['import', 'teamocil', './.teamocil/config.yaml'],
            ['\n', 'y\n', './la.yaml\n', 'y\n'],
        ),
        (
            ['import', 'teamocil', './.teamocil/config.yaml'],
            ['\n', 'y\n', './exists.yaml\n', './la.yaml\n', 'y\n'],
        ),
        (
            ['import', 'teamocil', 'config'],
            ['\n', 'y\n', './exists.yaml\n', './la.yaml\n', 'y\n'],
        ),
    ],
)
def test_import_teamocil(cli_args, inputs, tmpdir, monkeypatch):
    teamocil_config = loadfixture('config_teamocil/test4.yaml')
    teamocil_dir = tmpdir.join('.teamocil').mkdir()
    teamocil_dir.join('config.yaml').write(teamocil_config)
    tmpdir.join('exists.yaml').ensure()
    monkeypatch.setenv('HOME', str(tmpdir))

    with tmpdir.as_cwd():
        runner = CliRunner()
        runner.invoke(cli.cli, cli_args, input=''.join(inputs))
        assert tmpdir.join('la.yaml').check()


@pytest.mark.parametrize(
    "cli_args,inputs",
    [
        (
            ['import', 'tmuxinator', './.tmuxinator/config.yaml'],
            ['\n', 'y\n', './la.yaml\n', 'y\n'],
        ),
        (
            ['import', 'tmuxinator', './.tmuxinator/config.yaml'],
            ['\n', 'y\n', './exists.yaml\n', './la.yaml\n', 'y\n'],
        ),
        (
            ['import', 'tmuxinator', 'config'],
            ['\n', 'y\n', './exists.yaml\n', './la.yaml\n', 'y\n'],
        ),
    ],
)
def test_import_tmuxinator(cli_args, inputs, tmpdir, monkeypatch):
    tmuxinator_config = loadfixture('config_tmuxinator/test3.yaml')
    tmuxinator_dir = tmpdir.join('.tmuxinator').mkdir()
    tmuxinator_dir.join('config.yaml').write(tmuxinator_config)
    tmpdir.join('exists.yaml').ensure()
    monkeypatch.setenv('HOME', str(tmpdir))

    with tmpdir.as_cwd():
        runner = CliRunner()
        out = runner.invoke(cli.cli, cli_args, input=''.join(inputs))
        print(out.output)
        assert tmpdir.join('la.yaml').check()


@pytest.mark.parametrize(
    "cli_args,inputs",
    [
        (['freeze', 'mysession'], ['\n', 'y\n', './la.yaml\n', 'y\n']),
        (  # Exists
            ['freeze', 'mysession'],
            ['\n', 'y\n', './exists.yaml\n', './la.yaml\n', 'y\n'],
        ),
        (  # Imply current session if not entered
            ['freeze'],
            ['\n', 'y\n', './la.yaml\n', 'y\n'],
        ),
        (['freeze'], ['\n', 'y\n', './exists.yaml\n', './la.yaml\n', 'y\n']),  # Exists
    ],
)
def test_freeze(server, cli_args, inputs, tmpdir, monkeypatch):
    monkeypatch.setenv('HOME', str(tmpdir))
    tmpdir.join('exists.yaml').ensure()

    server.new_session(session_name='mysession')

    with tmpdir.as_cwd():
        runner = CliRunner()
        # Use tmux server (socket name) used in the test
        cli_args = cli_args + ['-L', server.socket_name]
        out = runner.invoke(cli.cli, cli_args, input=''.join(inputs))
        print(out.output)
        assert tmpdir.join('la.yaml').check()


def test_get_abs_path(tmpdir):
    expect = str(tmpdir)
    with tmpdir.as_cwd():
        cli.get_abs_path('../') == os.path.dirname(expect)
        cli.get_abs_path('.') == expect
        cli.get_abs_path('./') == expect
        cli.get_abs_path(expect) == expect


def test_get_tmuxinator_dir(monkeypatch):
    assert cli.get_tmuxinator_dir() == os.path.expanduser('~/.tmuxinator/')

    monkeypatch.setenv('HOME', '/moo')
    assert cli.get_tmuxinator_dir() == '/moo/.tmuxinator/'
    assert cli.get_tmuxinator_dir() == os.path.expanduser('~/.tmuxinator/')


def test_get_cwd(tmpdir):
    assert cli.get_cwd() == os.getcwd()

    with tmpdir.as_cwd():
        assert cli.get_cwd() == str(tmpdir)
        assert cli.get_cwd() == os.getcwd()


def test_get_teamocil_dir(monkeypatch):
    assert cli.get_teamocil_dir() == os.path.expanduser('~/.teamocil/')

    monkeypatch.setenv('HOME', '/moo')
    assert cli.get_teamocil_dir() == '/moo/.teamocil/'
    assert cli.get_teamocil_dir() == os.path.expanduser('~/.teamocil/')


def test_validate_choices():
    validate = cli._validate_choices(['choice1', 'choice2'])

    assert validate('choice1')
    assert validate('choice2')

    with pytest.raises(click.BadParameter):
        assert validate('choice3')


def test_pass_config_dir_ClickPath(tmpdir):
    configdir = tmpdir.join('myconfigdir')
    configdir.mkdir()
    user_config_name = 'myconfig'
    user_config = configdir.join('%s.yaml' % user_config_name).ensure()

    expect = str(configdir.join('myconfig.yaml'))

    runner = CliRunner()

    @click.command()
    @click.argument(
        'config',
        type=cli.ConfigPath(exists=True, config_dir=(str(configdir))),
        nargs=-1,
    )
    def config_cmd(config):
        click.echo(config)

    def check_cmd(config_arg):
        return runner.invoke(config_cmd, [config_arg]).output

    with configdir.as_cwd():
        assert expect in check_cmd('myconfig')
        assert expect in check_cmd('myconfig.yaml')
        assert expect in check_cmd('./myconfig.yaml')
        assert str(user_config) in check_cmd(str(configdir.join('myconfig.yaml')))

        assert 'file not found' in check_cmd('.tmuxp.json')
