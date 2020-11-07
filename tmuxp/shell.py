# -*- coding: utf-8 -*-
"""Utility and helper methods for tmuxp.

tmuxp.shell
~~~~~~~~~~~

"""
from __future__ import absolute_import, unicode_literals

import logging
import os

logger = logging.getLogger(__name__)


def launch(shell=None, best=True, use_pythonrc=False, **kwargs):
    import code

    import libtmux

    imported_objects = {
        'libtmux': libtmux,
        'Server': libtmux.Server,
        'Session': libtmux.Session,
        'Window': libtmux.Window,
        'Pane': libtmux.Pane,
        'server': kwargs.get('server'),
        'session': kwargs.get('session'),
        'window': kwargs.get('window'),
        'pane': kwargs.get('pane'),
    }

    try:
        # Try activating rlcompleter, because it's handy.
        import readline
    except ImportError:
        pass
    else:
        # We don't have to wrap the following import in a 'try', because
        # we already know 'readline' was imported successfully.
        import rlcompleter

        readline.set_completer(rlcompleter.Completer(imported_objects).complete)
        # Enable tab completion on systems using libedit (e.g. macOS).
        # These lines are copied from Lib/site.py on Python 3.4.
        readline_doc = getattr(readline, '__doc__', '')
        if readline_doc is not None and 'libedit' in readline_doc:
            readline.parse_and_bind("bind ^I rl_complete")
        else:
            readline.parse_and_bind("tab:complete")

    # We want to honor both $PYTHONSTARTUP and .pythonrc.py, so follow system
    # conventions and get $PYTHONSTARTUP first then .pythonrc.py.
    if use_pythonrc:
        for pythonrc in set(
            [os.environ.get("PYTHONSTARTUP"), os.path.expanduser('~/.pythonrc.py')]
        ):
            if not pythonrc:
                continue
            if not os.path.isfile(pythonrc):
                continue
            with open(pythonrc) as handle:
                pythonrc_code = handle.read()
            # Match the behavior of the cpython shell where an error in
            # PYTHONSTARTUP prints an exception and continues.
            try:
                exec(compile(pythonrc_code, pythonrc, 'exec'), imported_objects)
            except Exception:
                import traceback

                traceback.print_exc()

    code.interact(local=imported_objects)
