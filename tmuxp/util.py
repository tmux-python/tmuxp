# -*- coding: utf-8 -*-
"""Utility and helper methods for tmuxp.

tmuxp.util
~~~~~~~~~~

"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals, with_statement)

import logging
import os
import shlex
import subprocess
import sys

from . import exc
from ._compat import console_to_str

logger = logging.getLogger(__name__)

PY2 = sys.version_info[0] == 2


def run_before_script(script_file, cwd=None):
    """Function to wrap try/except for subprocess.check_call()."""
    try:
        proc = subprocess.Popen(
            shlex.split(str(script_file)),
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            cwd=cwd
        )
        for line in iter(proc.stdout.readline, b''):
            sys.stdout.write(console_to_str(line))
        proc.wait()

        if proc.returncode:
            stderr = proc.stderr.read()
            proc.stderr.close()
            stderr = console_to_str(stderr).split('\n')
            stderr = '\n'.join(list(filter(None, stderr)))  # filter empty

            raise exc.BeforeLoadScriptError(
                proc.returncode, os.path.abspath(script_file), stderr
            )

        return proc.returncode
    except OSError as e:
        if e.errno == 2:
            raise exc.BeforeLoadScriptNotExists(
                e, os.path.abspath(script_file)
            )
        else:
            raise e


def oh_my_zsh_auto_title():
    """Give warning and offer to fix ``DISABLE_AUTO_TITLE``.

    see: https://github.com/robbyrussell/oh-my-zsh/pull/257

    """

    if 'SHELL' in os.environ and 'zsh' in os.environ.get('SHELL'):
        if os.path.exists(os.path.expanduser('~/.oh-my-zsh')):
            # oh-my-zsh exists
            if (
                'DISABLE_AUTO_TITLE' not in os.environ or
                os.environ.get('DISABLE_AUTO_TITLE') == "false"
            ):
                print('Please set:\n\n'
                      '\texport DISABLE_AUTO_TITLE = \'true\'\n\n'
                      'in ~/.zshrc or where your zsh profile is stored.\n'
                      'Remember the "export" at the beginning!\n\n'
                      'Then create a new shell or type:\n\n'
                      '\t$ source ~/.zshrc')
