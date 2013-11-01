# -*- coding: utf8 - *-
"""For accessing tmuxp as a package.

tmuxp
~~~~~

:copyright: Copyright 2013 Tony Narlock.
:license: BSD, see LICENSE for details

"""

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
