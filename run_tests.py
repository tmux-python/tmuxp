#!/usr/bin/env python

def interact(line, stdin, process):
#    print line
    pass


import unittest
import sys
import os
from tmuxp import t
import tmuxp.testsuite

tmux_path = sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
if tmux_path not in sys.path:
    sys.path.insert(0, tmux_path)


def main():
    suites = unittest.TestLoader().discover('tmuxp.testsuite', pattern="*.py")

    unittest.TextTestRunner().run(suites)


if __name__ == '__main__':
    main()
