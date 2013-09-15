#!/usr/bin/env python

def interact(line, stdin, process):
#    print line
    pass


import unittest
import sys
import os
import subprocess
import argparse
import tmuxp.testsuite
from tmuxp.util import tmux
from tmuxp import t

tmux_path = sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
if tmux_path not in sys.path:
    sys.path.insert(0, tmux_path)

from time import sleep
import itertools


parser = argparse.ArgumentParser(description="test framework")
parser.add_argument('--pypid', type=int, required=False)

def main():

    t.socket_name = 'hi'

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

    tmuxclient = None
    if not in_tmux():
        shell_commands = []
        if has_virtualenv():
            shell_commands.append('source %s/bin/activate' % has_virtualenv())
        shell_commands.append('echo wat lol %s' % has_virtualenv())
        session_name = 'tmuxp'
        t.tmux('new-session', '-d', '-s', session_name)
        for shell_command in shell_commands:
            t.tmux('send-keys', '-t', session_name, shell_command, '^M')

        t.tmux('send-keys', '-R', '-t', session_name, 'python run_tests.py --pypid=%s' % os.getpid(), '^M')

        os.environ['pypid'] = str(os.getpid())

        #os.execl('/usr/local/bin/tmux', 'tmux', 'attach-session', '-t', session_name)
        t.hotswap(session_name=session_name)
        def output(line):
            #print(line)
            pass
        #tmuxclient = t.tmux('-C')
        #tmuxclient = subprocess.Popen(['tmux', '-C', '-Lhi', 'attach'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    else:
        print has_virtualenv()
        print in_tmux()
        print os.environ.get('pypid')
        args = vars(parser.parse_args())
        if 'pypid' in args:
            print args['pypid']
        suites = unittest.TestLoader().discover('tmuxp.testsuite', pattern="*.py")

        # todo create a hook to run after suite / loader to detach
        # and killall tmuxp + tmuxp_-prefixed sessions.
        #tmux('detach')
        #os.kill(args['pypid'], 9)
        #t.kill_server()
        return unittest.TextTestRunner(verbosity=2).run(suites)

if __name__ == '__main__':
    main()
