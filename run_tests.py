#!/usr/bin/env python

def interact(line, stdin, process):
#    print line
    pass


import unittest
import sys
import os
import subprocess
from tmuxp import t
import tmuxp.testsuite
from tmuxp.util import tmux

tmux_path = sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
if tmux_path not in sys.path:
    sys.path.insert(0, tmux_path)

tmuxprocess = subprocess.Popen(['tmux', '-C'])
tmux('set-option', '-g', 'detach-on-destroy', 'off')

def main():
    suites = unittest.TestLoader().discover('tmuxp.testsuite', pattern="*.py")

    unittest.TextTestRunner().run(suites)
    tmuxprocess.kill()


if __name__ == '__main__':
    main()
