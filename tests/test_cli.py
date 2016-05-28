# -*- coding: utf-8 -*-
"""Test for tmuxp command line interface."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals, with_statement)

import os

from tmuxp import cli, config


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
