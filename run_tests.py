#!/usr/bin/env python
import unittest
import sys
import os
from tmux import t

tmux_path = sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
if tmux_path not in sys.path:
    sys.path.insert(0, tmux_path)


def main():
    if t.has_clients():
        #unittest.main()
        suites = unittest.TestLoader().discover(".", pattern="*.py")

        unittest.TextTestRunner().run(suites)
    else:
        print('must have a tmux client running')


if __name__ == '__main__':
    main()
