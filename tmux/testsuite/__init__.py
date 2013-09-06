# -*- coding: utf-8 -*-
"""
    tmuxwrapper.tests
    ~~~~~~~~~~~~~~~~~

    :copyright: Copyright 2013 Tony Narlock <tony@git-pull.com>.
    :license: BSD, see LICENSE for details

    this can be ran like::

        nosetests tests.py

    or::

        python tests.py

    also, if you have ``node`` and ``npm`` you may (sudo)::

        ``npm install -g nodemon``
        ``nodemon --watch tests.py --watch main.py --exec "nosetests" tests.py

    or::

        ``nodemon --watch tests.py --watch main.py --exec "python" tests.py

    These tests require an active tmux client open while it runs. It is best to
    have a second terminal with tmux running alongside the terminal running the
    tests.
"""

import unittest
from tmux import t


def main():
    if t.has_clients():
        #unittest.main()
        suites = unittest.TestLoader().discover(".", pattern="*.py")

        unittest.TextTestRunner().run(suites)
    else:
        print('must have a tmux client running')

#if __name__ == '__main__':
#    main()
