# -*- coding: utf-8 -*-
"""Tests for utility functions in tmux.

tmuxp.tests.util
~~~~~~~~~~~~~~~~

"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals, with_statement)

import logging
import os
import re

import pytest

from libtmux.common import has_required_tmux_version
from libtmux.exc import LibTmuxException
from tmuxp import exc
from tmuxp.exc import BeforeLoadScriptError, BeforeLoadScriptNotExists
from tmuxp.util import run_before_script

from . import fixtures_dir

logger = logging.getLogger(__name__)

version_regex = re.compile(r'[0-9]\.[0-9]')


def test_no_arg_uses_tmux_version():
    """Test the :meth:`has_required_tmux_version`."""
    result = has_required_tmux_version()
    assert version_regex.match(result) is not None


def test_ignores_letter_versions():
    """Ignore letters such as 1.8b.

    See ticket https://github.com/tony/tmuxp/issues/55.

    In version 0.1.7 this is adjusted to use LooseVersion, in order to
    allow letters.

    """
    result = has_required_tmux_version('1.9a')
    assert version_regex.match(result) is not None

    result = has_required_tmux_version('1.8a')
    assert result == r'1.8'


def test_error_version_less_1_7():
    with pytest.raises(LibTmuxException) as excinfo:
        has_required_tmux_version('1.7')
        excinfo.match(r'tmuxp only supports')

    with pytest.raises(LibTmuxException) as excinfo:
        has_required_tmux_version('1.6a')

        excinfo.match(r'tmuxp only supports')

    has_required_tmux_version('1.9a')


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
