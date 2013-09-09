#!/usr/bin/env python
import unittest
import sys
import os
from tmuxp import t
import tmuxp.testsuite
try:
    from sh import tmux as tmux, ErrorReturnCode_1
except ImportError:
    logging.warning('tmux must be installed and in PATH\'s to use tmuxp')


tmux_path = sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
if tmux_path not in sys.path:
    sys.path.insert(0, tmux_path)


def interact(line, stdin, process):
#    print line
    pass

tmux('-C', _out=interact)


def main():
    if t.has_clients():
        #unittest.main()
        suites = unittest.TestLoader().discover('tmuxp.testsuite', pattern="*.py")

        unittest.TextTestRunner().run(suites)
    else:
        raise Exception('must have a tmux client running')


if __name__ == '__main__':
    main()
