# -*- coding: utf-8 -*-
"""For accessing tmuxp as a package.

tmuxp
~~~~~

"""
from __future__ import absolute_import, division, print_function, \
    with_statement, unicode_literals

import sys
import os


def run():
    """Assure tmuxp is in python path's and available as a package. """
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, base)
    import tmuxp.cli
    tmuxp.cli.main()

if __name__ == '__main__':
    exit = run()
    if exit:
        sys.exit(exit)
