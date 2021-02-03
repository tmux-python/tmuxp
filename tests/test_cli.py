# -*- coding: utf-8 -*-
"""Test for tmuxp command line interface."""
from __future__ import absolute_import

import json
import os

try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock

import pytest

import click
import kaptan
from click.testing import CliRunner

import libtmux
from libtmux.common import has_lt_version
from libtmux.exc import LibTmuxException
from tmuxp import cli, config, exc
from tmuxp.cli import (
    _load_append_windows_to_current_session,
    _load_attached,
    _reattach,
    command_debug_info,
    command_ls,
    get_config_dir,
    is_pure_name,
    load_plugins,
    load_workspace,
    scan_config,
)
from tmuxp.workspacebuilder import WorkspaceBuilder

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


def test_load_workspace_named_session(server, monkeypatch):
    # this is an implementation test. Since this testsuite may be ran within
    # a tmux session by the developer himself, delete the TMUX variable
    # temporarily.
    monkeypatch.delenv('TMUX', raising=False)
    session_file = curjoin("workspacebuilder/two_pane.yaml")

    # open it detached
    session = load_workspace(
        session_file,
        socket_name=server.socket_name,
        new_session_name='tmuxp-new',
        detached=True,
    )

    assert isinstance(session, libtmux.Session)
    assert session.name == 'tmuxp-new'


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


@pytest.mark.parametrize(
    "cli_args",
    [
        (['load', '.', '--log-file', 'log.txt']),
    ],
)
def test_load_log_file(cli_args, tmpdir, monkeypatch):
    # create dummy tmuxp yaml that breaks to prevent actually loading tmux
    tmpdir.join('.tmuxp.yaml').write(
        """
session_name: hello
        """
    )
    tmpdir.join('.oh-my-zsh').ensure(dir=True)
    monkeypatch.setenv('HOME', str(tmpdir))

    with tmpdir.as_cwd():
        print('tmpdir: {0}'.format(tmpdir))
        runner = CliRunner()

        # If autoconfirm (-y) no need to prompt y
        input_args = 'y\ny\n' if '-y' not in cli_args else ''

        runner.invoke(cli.cli, cli_args, input=input_args)
        assert 'Loading' in tmpdir.join('log.txt').open().read()


@pytest.mark.parametrize("cli_cmd", ['shell', ('shell', '--pdb')])
@pytest.mark.parametrize(
    "cli_args,inputs,env,expected_output",
    [
        (
            ['-L{SOCKET_NAME}', '-c', 'print(str(server.socket_name))'],
            [],
            {},
            '{SERVER_SOCKET_NAME}',
        ),
        (
            [
                '-L{SOCKET_NAME}',
                '{SESSION_NAME}',
                '-c',
                'print(session.name)',
            ],
            [],
            {},
            '{SESSION_NAME}',
        ),
        (
            [
                '-L{SOCKET_NAME}',
                '{SESSION_NAME}',
                '{WINDOW_NAME}',
                '-c',
                'print(server.has_session(session.name))',
            ],
            [],
            {},
            'True',
        ),
        (
            [
                '-L{SOCKET_NAME}',
                '{SESSION_NAME}',
                '{WINDOW_NAME}',
                '-c',
                'print(window.name)',
            ],
            [],
            {},
            '{WINDOW_NAME}',
        ),
        (
            [
                '-L{SOCKET_NAME}',
                '{SESSION_NAME}',
                '{WINDOW_NAME}',
                '-c',
                'print(pane.id)',
            ],
            [],
            {},
            '{PANE_ID}',
        ),
        (
            [
                '-L{SOCKET_NAME}',
                '-c',
                'print(pane.id)',
            ],
            [],
            {'TMUX_PANE': '{PANE_ID}'},
            '{PANE_ID}',
        ),
    ],
)
def test_shell(
    cli_cmd,
    cli_args,
    inputs,
    expected_output,
    env,
    tmpdir,
    monkeypatch,
    server,
    session,
):
    monkeypatch.setenv('HOME', str(tmpdir))
    window_name = 'my_window'
    window = session.new_window(window_name=window_name)
    window.split_window()

    template_ctx = dict(
        SOCKET_NAME=server.socket_name,
        SOCKET_PATH=server.socket_path,
        SESSION_NAME=session.name,
        WINDOW_NAME=window_name,
        PANE_ID=window.attached_pane.id,
        SERVER_SOCKET_NAME=server.socket_name,
    )

    cli_cmd = list(cli_cmd) if isinstance(cli_cmd, (list, tuple)) else [cli_cmd]
    cli_args = cli_cmd + [cli_arg.format(**template_ctx) for cli_arg in cli_args]

    for k, v in env.items():
        monkeypatch.setenv(k, v.format(**template_ctx))

    with tmpdir.as_cwd():
        runner = CliRunner()

        result = runner.invoke(
            cli.cli, cli_args, input=''.join(inputs), catch_exceptions=False
        )
        assert expected_output.format(**template_ctx) in result.output


@pytest.mark.parametrize(
    "cli_cmd",
    [
        'shell',
        ('shell', '--pdb'),
    ],
)
@pytest.mark.parametrize(
    "cli_args,inputs,env,template_ctx,exception,message",
    [
        (
            ['-LDoesNotExist', '-c', 'print(str(server.socket_name))'],
            [],
            {},
            {},
            LibTmuxException,
            r'.*DoesNotExist.*',
        ),
        (
            [
                '-L{SOCKET_NAME}',
                'nonexistant_session',
                '-c',
                'print(str(server.socket_name))',
            ],
            [],
            {},
            {'session_name': 'nonexistant_session'},
            exc.TmuxpException,
            'Session not found: nonexistant_session',
        ),
        (
            [
                '-L{SOCKET_NAME}',
                '{SESSION_NAME}',
                'nonexistant_window',
                '-c',
                'print(str(server.socket_name))',
            ],
            [],
            {},
            {'window_name': 'nonexistant_window'},
            exc.TmuxpException,
            'Window not found: {WINDOW_NAME}',
        ),
    ],
)
def test_shell_target_missing(
    cli_cmd,
    cli_args,
    inputs,
    env,
    template_ctx,
    exception,
    message,
    tmpdir,
    monkeypatch,
    socket_name,
    server,
    session,
):
    monkeypatch.setenv('HOME', str(tmpdir))
    window_name = 'my_window'
    window = session.new_window(window_name=window_name)
    window.split_window()

    template_ctx = dict(
        SOCKET_NAME=server.socket_name,
        SOCKET_PATH=server.socket_path,
        SESSION_NAME=session.name,
        WINDOW_NAME=template_ctx.get('window_name', window_name),
        PANE_ID=template_ctx.get('pane_id'),
        SERVER_SOCKET_NAME=server.socket_name,
    )
    cli_cmd = list(cli_cmd) if isinstance(cli_cmd, (list, tuple)) else [cli_cmd]
    cli_args = cli_cmd + [cli_arg.format(**template_ctx) for cli_arg in cli_args]

    for k, v in env.items():
        monkeypatch.setenv(k, v.format(**template_ctx))

    with tmpdir.as_cwd():
        runner = CliRunner()

        if exception is not None:
            with pytest.raises(exception, match=message.format(**template_ctx)):
                result = runner.invoke(
                    cli.cli, cli_args, input=''.join(inputs), catch_exceptions=False
                )
        else:
            result = runner.invoke(
                cli.cli, cli_args, input=''.join(inputs), catch_exceptions=False
            )
            assert message.format(**template_ctx) in result.output


@pytest.mark.parametrize(
    "cli_cmd",
    [
        # 'shell',
        # ('shell', '--pdb'),
        ('shell', '--code'),
        # ('shell', '--bpython'),
        # ('shell', '--ptipython'),
        # ('shell', '--ptpython'),
        # ('shell', '--ipython'),
    ],
)
@pytest.mark.parametrize(
    "cli_args,inputs,env,message",
    [
        (
            [
                '-L{SOCKET_NAME}',
            ],
            [],
            {},
            '(InteractiveConsole)',
        ),
        (
            [
                '-L{SOCKET_NAME}',
            ],
            [],
            {'PANE_ID': '{PANE_ID}'},
            '(InteractiveConsole)',
        ),
    ],
)
def test_shell_plus(
    cli_cmd,
    cli_args,
    inputs,
    env,
    message,
    tmpdir,
    monkeypatch,
    server,
    session,
):
    monkeypatch.setenv('HOME', str(tmpdir))
    window_name = 'my_window'
    window = session.new_window(window_name=window_name)
    window.split_window()

    template_ctx = dict(
        SOCKET_NAME=server.socket_name,
        SOCKET_PATH=server.socket_path,
        SESSION_NAME=session.name,
        WINDOW_NAME=window_name,
        PANE_ID=window.attached_pane.id,
        SERVER_SOCKET_NAME=server.socket_name,
    )

    cli_cmd = list(cli_cmd) if isinstance(cli_cmd, (list, tuple)) else [cli_cmd]
    cli_args = cli_cmd + [cli_arg.format(**template_ctx) for cli_arg in cli_args]

    for k, v in env.items():
        monkeypatch.setenv(k, v.format(**template_ctx))

    with tmpdir.as_cwd():
        runner = CliRunner()

        result = runner.invoke(
            cli.cli, cli_args, input=''.join(inputs), catch_exceptions=True
        )
        assert message.format(**template_ctx) in result.output


@pytest.mark.parametrize(
    "cli_args",
    [
        (['convert', '.']),
        (['convert', '.tmuxp.yaml']),
        (['convert', '.tmuxp.yaml', '-y']),
    ],
)
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

        # If autoconfirm (-y) no need to prompt y
        input_args = 'y\ny\n' if '-y' not in cli_args else ''

        runner.invoke(cli.cli, cli_args, input=input_args)
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
        (  # Create a new one
            ['freeze', 'mysession', '--force'],
            ['\n', 'y\n', './la.yaml\n', 'y\n'],
        ),
        (  # Imply current session if not entered
            ['freeze', '--force'],
            ['\n', 'y\n', './la.yaml\n', 'y\n'],
        ),
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


@pytest.mark.parametrize(
    "cli_args,inputs",
    [
        (  # Overwrite
            ['freeze', 'mysession', '--force'],
            ['\n', 'y\n', './exists.yaml\n', 'y\n'],
        ),
        (  # Imply current session if not entered
            ['freeze', '--force'],
            ['\n', 'y\n', './exists.yaml\n', 'y\n'],
        ),
    ],
)
def test_freeze_overwrite(server, cli_args, inputs, tmpdir, monkeypatch):
    monkeypatch.setenv('HOME', str(tmpdir))
    tmpdir.join('exists.yaml').ensure()

    server.new_session(session_name='mysession')

    with tmpdir.as_cwd():
        runner = CliRunner()
        # Use tmux server (socket name) used in the test
        cli_args = cli_args + ['-L', server.socket_name]
        out = runner.invoke(cli.cli, cli_args, input=''.join(inputs))
        print(out.output)
        assert tmpdir.join('exists.yaml').check()


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


def test_ls_cli(monkeypatch, tmpdir):
    monkeypatch.setenv("HOME", str(tmpdir))

    filenames = [
        '.git/',
        '.gitignore/',
        'session_1.yaml',
        'session_2.yaml',
        'session_3.json',
        'session_4.txt',
    ]

    # should ignore:
    # - directories should be ignored
    # - extensions not covered in VALID_CONFIG_DIR_FILE_EXTENSIONS
    ignored_filenames = ['.git/', '.gitignore/', 'session_4.txt']
    stems = [os.path.splitext(f)[0] for f in filenames if f not in ignored_filenames]

    for filename in filenames:
        location = tmpdir.join('.tmuxp/{}'.format(filename))
        if filename.endswith('/'):
            location.ensure_dir()
        else:
            location.ensure()

    runner = CliRunner()
    cli_output = runner.invoke(command_ls).output
    assert cli_output == '\n'.join(stems) + '\n'


def test_load_plugins(monkeypatch_plugin_test_packages):
    from tmuxp_test_plugin_bwb.plugin import PluginBeforeWorkspaceBuilder

    plugins_config = loadfixture("workspacebuilder/plugin_bwb.yaml")

    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(plugins_config).get()
    sconfig = config.expand(sconfig)

    plugins = load_plugins(sconfig)

    assert len(plugins) == 1

    test_plugin_class_types = [
        PluginBeforeWorkspaceBuilder().__class__,
    ]
    for plugin in plugins:
        assert plugin.__class__ in test_plugin_class_types


@pytest.mark.skip('Not sure how to clean up the tmux session this makes')
@pytest.mark.parametrize(
    "cli_args,inputs",
    [
        (
            ['load', 'tests/fixtures/workspacebuilder/plugin_versions_fail.yaml'],
            ['y\n'],
        )
    ],
)
def test_load_plugins_version_fail_skip(
    monkeypatch_plugin_test_packages, cli_args, inputs
):
    runner = CliRunner()

    results = runner.invoke(cli.cli, cli_args, input=''.join(inputs))
    assert '[Loading]' in results.output


@pytest.mark.parametrize(
    "cli_args,inputs",
    [
        (
            ['load', 'tests/fixtures/workspacebuilder/plugin_versions_fail.yaml'],
            ['n\n'],
        )
    ],
)
def test_load_plugins_version_fail_no_skip(
    monkeypatch_plugin_test_packages, cli_args, inputs
):
    runner = CliRunner()

    results = runner.invoke(cli.cli, cli_args, input=''.join(inputs))
    assert '[Not Skipping]' in results.output


@pytest.mark.parametrize(
    "cli_args", [(['load', 'tests/fixtures/workspacebuilder/plugin_missing_fail.yaml'])]
)
def test_load_plugins_plugin_missing(monkeypatch_plugin_test_packages, cli_args):
    runner = CliRunner()

    results = runner.invoke(cli.cli, cli_args)
    assert '[Plugin Error]' in results.output


def test_plugin_system_before_script(
    monkeypatch_plugin_test_packages, server, monkeypatch
):
    # this is an implementation test. Since this testsuite may be ran within
    # a tmux session by the developer himself, delete the TMUX variable
    # temporarily.
    monkeypatch.delenv('TMUX', raising=False)
    session_file = curjoin("workspacebuilder/plugin_bs.yaml")

    # open it detached
    session = load_workspace(
        session_file, socket_name=server.socket_name, detached=True
    )

    assert isinstance(session, libtmux.Session)
    assert session.name == 'plugin_test_bs'


def test_reattach_plugins(monkeypatch_plugin_test_packages, server):
    config_plugins = loadfixture("workspacebuilder/plugin_r.yaml")

    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(config_plugins).get()
    sconfig = config.expand(sconfig)

    # open it detached
    builder = WorkspaceBuilder(
        sconf=sconfig, plugins=load_plugins(sconfig), server=server
    )
    builder.build()

    try:
        _reattach(builder)
    except libtmux.exc.LibTmuxException:
        pass

    proc = builder.session.cmd('display-message', '-p', "'#S'")

    assert proc.stdout[0] == "'plugin_test_r'"


def test_load_attached(server, monkeypatch):
    # Load a session and attach from outside tmux
    monkeypatch.delenv('TMUX', raising=False)

    attach_session_mock = MagicMock()
    attach_session_mock.return_value.stderr = None

    monkeypatch.setattr("libtmux.session.Session.attach_session", attach_session_mock)

    yaml_config = loadfixture("workspacebuilder/two_pane.yaml")
    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(yaml_config).get()

    builder = WorkspaceBuilder(sconf=sconfig, server=server)

    _load_attached(builder, False)

    assert builder.session.attach_session.call_count == 1


def test_load_attached_detached(server, monkeypatch):
    # Load a session but don't attach
    monkeypatch.delenv('TMUX', raising=False)

    attach_session_mock = MagicMock()
    attach_session_mock.return_value.stderr = None

    monkeypatch.setattr("libtmux.session.Session.attach_session", attach_session_mock)

    yaml_config = loadfixture("workspacebuilder/two_pane.yaml")
    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(yaml_config).get()

    builder = WorkspaceBuilder(sconf=sconfig, server=server)

    _load_attached(builder, True)

    assert builder.session.attach_session.call_count == 0


def test_load_attached_within_tmux(server, monkeypatch):
    # Load a session and attach from within tmux
    monkeypatch.setenv('TMUX', "/tmp/tmux-1234/default,123,0")

    switch_client_mock = MagicMock()
    switch_client_mock.return_value.stderr = None

    monkeypatch.setattr("libtmux.session.Session.switch_client", switch_client_mock)

    yaml_config = loadfixture("workspacebuilder/two_pane.yaml")
    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(yaml_config).get()

    builder = WorkspaceBuilder(sconf=sconfig, server=server)

    _load_attached(builder, False)

    assert builder.session.switch_client.call_count == 1


def test_load_attached_within_tmux_detached(server, monkeypatch):
    # Load a session and attach from within tmux
    monkeypatch.setenv('TMUX', "/tmp/tmux-1234/default,123,0")

    switch_client_mock = MagicMock()
    switch_client_mock.return_value.stderr = None

    monkeypatch.setattr("libtmux.session.Session.switch_client", switch_client_mock)

    yaml_config = loadfixture("workspacebuilder/two_pane.yaml")
    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(yaml_config).get()

    builder = WorkspaceBuilder(sconf=sconfig, server=server)

    _load_attached(builder, True)

    assert builder.session.switch_client.call_count == 1


def test_load_append_windows_to_current_session(server, monkeypatch):
    yaml_config = loadfixture("workspacebuilder/two_pane.yaml")
    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(yaml_config).get()

    builder = WorkspaceBuilder(sconf=sconfig, server=server)
    builder.build()

    assert len(server.list_sessions()) == 1
    assert len(server._list_windows()) == 3

    # Assign an active pane to the session
    monkeypatch.setenv("TMUX_PANE", server._list_panes()[0]["pane_id"])

    builder = WorkspaceBuilder(sconf=sconfig, server=server)
    _load_append_windows_to_current_session(builder)

    assert len(server.list_sessions()) == 1
    assert len(server._list_windows()) == 6


def test_debug_info_cli(monkeypatch, tmpdir):
    monkeypatch.setenv('SHELL', '/bin/bash')

    runner = CliRunner()
    cli_output = runner.invoke(command_debug_info).output
    assert 'environment' in cli_output
    assert 'python version' in cli_output
    assert 'system PATH' in cli_output
    assert 'tmux version' in cli_output
    assert 'libtmux version' in cli_output
    assert 'tmuxp version' in cli_output
    assert 'tmux path' in cli_output
    assert 'tmuxp path' in cli_output
    assert 'shell' in cli_output
    assert 'tmux session' in cli_output
    assert 'tmux windows' in cli_output
    assert 'tmux panes' in cli_output
    assert 'tmux global options' in cli_output
    assert 'tmux window options' in cli_output
