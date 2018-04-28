# -*- coding: utf-8 -*-
"""Tests for utility functions in tmux."""

from __future__ import absolute_import, unicode_literals

import os

import pytest

from tmuxp import exc
from tmuxp.exc import BeforeLoadScriptError, BeforeLoadScriptNotExists
from tmuxp.util import run_before_script

from . import fixtures_dir


def test_raise_BeforeLoadScriptNotExists_if_not_exists():
    script_file = os.path.join(fixtures_dir, 'script_noexists.sh')

    with pytest.raises(BeforeLoadScriptNotExists):
        run_before_script(script_file)

    with pytest.raises(OSError):
        run_before_script(script_file)


def test_raise_BeforeLoadScriptError_if_retcode():
    script_file = os.path.join(fixtures_dir, 'script_failed.sh')

    with pytest.raises(BeforeLoadScriptError):
        run_before_script(script_file)


def test_return_stdout_if_ok(capsys):
    script_file = os.path.join(fixtures_dir, 'script_complete.sh')

    run_before_script(script_file)
    out, err = capsys.readouterr()
    assert 'hello' in out


def test_beforeload_returncode():
    script_file = os.path.join(fixtures_dir, 'script_failed.sh')

    with pytest.raises(exc.BeforeLoadScriptError) as excinfo:
        run_before_script(script_file)
        assert excinfo.match(r'113')


def test_beforeload_returns_stderr_messages():
    script_file = os.path.join(fixtures_dir, 'script_failed.sh')

    with pytest.raises(exc.BeforeLoadScriptError) as excinfo:
        run_before_script(script_file)
        assert excinfo.match(r'failed with returncode')
