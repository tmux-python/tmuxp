# -*- coding: utf-8 -*-
"""Utility and helper methods for tmuxp.

tmuxp.shell
~~~~~~~~~~~

"""
from __future__ import absolute_import, unicode_literals

import logging
import os

logger = logging.getLogger(__name__)


def has_ipython():
    try:
        from IPython import start_ipython  # NOQA F841
    except ImportError:
        try:
            from IPython.Shell import IPShell  # NOQA F841
        except ImportError:
            return False

    return True


def has_ptpython():
    try:
        from ptpython.repl import embed, run_config  # NOQA F841
    except ImportError:
        try:
            from prompt_toolkit.contrib.repl import embed, run_config  # NOQA F841
        except ImportError:
            return False

    return True


def has_ptipython():
    try:
        from ptpython.ipython import embed  # NOQA F841
        from ptpython.repl import run_config  # NOQA F841
    except ImportError:
        try:
            from prompt_toolkit.contrib.ipython import embed  # NOQA F841
            from prompt_toolkit.contrib.repl import run_config  # NOQA F841
        except ImportError:
            return False

    return True


def has_bpython():
    try:
        from bpython import embed  # NOQA F841
    except ImportError:
        return False
    return True


def detect_best_shell():
    if has_ptipython():
        return 'ptipython'
    elif has_ptpython():
        return 'ptpython'
    elif has_ipython():
        return 'ipython'
    elif has_bpython():
        return 'bpython'
    return 'code'


def get_bpython(options, extra_args=None):
    if extra_args is None:
        extra_args = {}

    from bpython import embed  # NOQA F841

    def launch_bpython():
        imported_objects = get_launch_args(**options)
        kwargs = {}
        if extra_args:
            kwargs['args'] = extra_args
        embed(imported_objects, **kwargs)

    return launch_bpython


def get_ipython_arguments():
    ipython_args = 'IPYTHON_ARGUMENTS'
    return os.environ.get(ipython_args, '').split()


def get_ipython(options, **extra_args):
    try:
        from IPython import start_ipython

        def launch_ipython():
            imported_objects = get_launch_args(**options)
            ipython_arguments = extra_args or get_ipython_arguments()
            start_ipython(argv=ipython_arguments, user_ns=imported_objects)

        return launch_ipython
    except ImportError:
        # IPython < 0.11
        # Explicitly pass an empty list as arguments, because otherwise
        # IPython would use sys.argv from this script.
        # Notebook not supported for IPython < 0.11.
        from IPython.Shell import IPShell

        def launch_ipython():
            imported_objects = get_launch_args(**options)
            shell = IPShell(argv=[], user_ns=imported_objects)
            shell.mainloop()

        return launch_ipython


def get_ptpython(options, vi_mode=False):
    try:
        from ptpython.repl import embed, run_config
    except ImportError:
        from prompt_toolkit.contrib.repl import embed, run_config

    def launch_ptpython():
        imported_objects = get_launch_args(**options)
        history_filename = os.path.expanduser('~/.ptpython_history')
        embed(
            globals=imported_objects,
            history_filename=history_filename,
            vi_mode=vi_mode,
            configure=run_config,
        )

    return launch_ptpython


def get_ptipython(options, vi_mode=False):
    """Based on django-extensions

    Run renamed to launch, get_imported_objects renamed to get_launch_args
    """
    try:
        from ptpython.ipython import embed
        from ptpython.repl import run_config
    except ImportError:
        # prompt_toolkit < v0.27
        from prompt_toolkit.contrib.ipython import embed
        from prompt_toolkit.contrib.repl import run_config

    def launch_ptipython():
        imported_objects = get_launch_args(**options)
        history_filename = os.path.expanduser('~/.ptpython_history')
        embed(
            user_ns=imported_objects,
            history_filename=history_filename,
            vi_mode=vi_mode,
            configure=run_config,
        )

    return launch_ptipython


def get_launch_args(**kwargs):
    import libtmux

    return {
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


def get_code(use_pythonrc, imported_objects):
    import code

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
            exec(compile(pythonrc_code, pythonrc, 'exec'), imported_objects)

    def launch_code():
        code.interact(local=imported_objects)

    return launch_code


def launch(shell='best', use_pythonrc=False, use_vi_mode=False, **kwargs):
    # Also allowing passing shell='code' to force using code.interact
    imported_objects = get_launch_args(**kwargs)

    if shell == 'best':
        shell = detect_best_shell()

    if shell == 'ptipython':
        launch = get_ptipython(options=kwargs, vi_mode=use_vi_mode)
    elif shell == 'ptpython':
        launch = get_ptpython(options=kwargs, vi_mode=use_vi_mode)
    elif shell == 'ipython':
        launch = get_ipython(options=kwargs)
    elif shell == 'bpython':
        launch = get_bpython(options=kwargs)
    else:
        launch = get_code(use_pythonrc=use_pythonrc, imported_objects=imported_objects)

    launch()
