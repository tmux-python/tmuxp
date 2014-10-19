
import os
import termstyle

from sniffer.api import file_validator, runnable

from tmuxp.testsuite import main

# you can customize the pass/fail colors like this
pass_fg_color = termstyle.green
pass_bg_color = termstyle.bg_default
fail_fg_color = termstyle.red
fail_bg_color = termstyle.bg_default

# All lists in this variable will be under surveillance for changes.
watch_paths = ['tmuxp/']


@file_validator
def py_files(filename):
    return filename.endswith('.py') and not os.path.basename(filename).startswith('.') and filename != ".tmuxp"


@runnable
def execute_nose(*args):
    try:
        return main()
    except SystemExit as x:
        if x.message:
            print "Found error {0}: {1}".format(x.code, x.message)
            return not x.code
        else:
            return 1

