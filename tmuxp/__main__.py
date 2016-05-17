# -*- coding: utf-8 -*-
"""For accessing tmuxp as a package.

tmuxp
~~~~~

"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals, with_statement)

import os
import sys


def run():
    """Assure tmuxp is in python path's and available as a package. """
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, base)
    import tmuxp.cli
    tmuxp.cli.main()

if __name__ == '__main__':
    _exit = run()
    if exit:
        sys.exit(_exit)
