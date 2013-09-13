#!/usr/bin/env python

def interact(line, stdin, process):
#    print line
    pass


import unittest
import sys
import os
import subprocess
import tmuxp.testsuite
from tmuxp.util import tmux

tmux_path = sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
if tmux_path not in sys.path:
    sys.path.insert(0, tmux_path)

from time import sleep
import itertools

def main():

    def has_virtualenv():
        if os.environ.get('VIRTUAL_ENV'):
            return os.environ.get('VIRTUAL_ENV')
        else:
            False

    def in_tmux():
        if os.environ.get('TMUX'):
            return True
        else:
            return False

    if not in_tmux():
        shell_commands = []
        if has_virtualenv():
            shell_commands.append('source %s/bin/activate' % has_virtualenv())
        shell_commands.append('echo wat lol %s' % has_virtualenv())
        session_name = 'tmuxp'
        tmux('new-session', '-d', '-s', session_name)
        for shell_command in shell_commands:
            tmux('send-keys', '-t', session_name, shell_command, '^M')

        tmux('send-keys', '-R', '-t', session_name, 'python run_tests.py', '^M')

        os.environ['pypid'] = str(os.getpid())

        os.execl('/usr/local/bin/tmux', 'tmux', 'attach-session', '-t', session_name)
        #subprocess.Popen(['tmux', 'attach-session', '-t', session_name])
    else:
        print has_virtualenv()
        print in_tmux()
        print os.environ.get('pypid')
        suites = unittest.TestLoader().discover('tmuxp.testsuite', pattern="*.py")
        unittest.TextTestRunner(verbosity=2).run(suites)
        # todo create a hook to run after suite / loader to detach
        # and killall tmuxp + tmuxp_-prefixed sessions.
        tmux('detach')

if __name__ == '__main__':
    main()
