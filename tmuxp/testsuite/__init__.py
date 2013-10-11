# -*- coding: utf-8 -*-
"""
    tmuxp.tests
    ~~~~~~~~~~~

    :copyright: Copyright 2013 Tony Narlock.
    :license: BSD, see LICENSE for details

    To test, first make a virtual environment, to learn more see:

    http://docs.python-guide.org/en/latest/dev/virtualenvs/

    A quick setup, if ``virtualenv`` is installed (inside of project)::

        virtualenv .env
        pip install -r requirements.pip

    this can be ran like:

        $ python run_tests.py

    with ``pip install ipython``:

        ipython tmux/testsuite/*.py

    with ``pip install bpython``:

        bpython tmux/testsuite/*.py

    with ``pip install nosetests``:

        nosetests tmux/testsuite/*.py

    or with ``pip install pytest``:

        py.test tmux/testsuite/*.py

    You can also use the ``nosetests`` or ``pytests`` to run the test, it will
    handle the package imports. ``python`` will give error, "Attmpted relative
    import in non-package".

        nosetests ./tmux/testsuite/builder.py

    If you use install node (http://www.nodejs.org) on your system, you can use
    nodemon::

        sudo npm install -g nodemon
        nodemon -e py --exec "python" run_tests.py

    or::

        nodemon -e py --exec "py.test" tmux/testsuite/*.py

    These tests require an active tmux client open while it runs. It is best to
    have a second terminal with tmux running alongside the terminal running the
    tests.
"""

from ..server import Server
t = Server()
t.socket_name = 'tmuxp_test'

from .. import log
import logging
logger = logging.getLogger()


if not logger.handlers:
    channel = logging.StreamHandler()
    channel.setFormatter(log.DebugLogFormatter())
    logger.addHandler(channel)
    logger.setLevel('INFO')

    # enable DEBUG message if channel is at testsuite + testsuite.* packages.
    testsuite_logger = logging.getLogger(__name__)

    testsuite_logger.setLevel('INFO')
