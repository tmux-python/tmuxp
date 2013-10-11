.. _developing:

======================
Developing and Testing
======================

.. todo::
    link to sliderepl or ipython notebook slides

.. important::

    We are trying to make tmuxp stable and friendly as possible. If
    something in these instructions is not working, or you need help,
    please file an `issue on github`_ with your tmux version ``tmux -V``,
    OS, and any other information that would be helpful to assess.

Testing
-------

Our tests are inside ``./tmuxp/testsuite``. Tests are implemented using
:py:mod:`unittest`.

``./run_tests.py`` will create a tmux server on a separate ``socket_name``
using ``$ tmux -L test_case``.

.. _install_dev_env:

Install the latest code
"""""""""""""""""""""""

To begin developing, check out the code from github:

.. code-block:: bash

    $ git clone git@github.com:tony/tmuxp.git
    $ cd tmuxp

Now create a virtualenv, if you don't know how to, you can create a
virtualenv with:

.. code-block:: bash

    $ virtualenv .env

Then activate it to your current tty / terminal session with:

.. code-block:: bash

    $ source .env/bin/activate

Good! Now let's run this:

.. code-block:: bash

    $ pip install -e .

This has ``pip``, a python package manager install the python package
in the current directory. ``-e`` means ``--editable``, which means you can
adjust the code and the installed software will reflect the changes.

.. code-block:: bash

    $ tmuxp


Run tests
"""""""""

As you seen above, the ``tmuxp`` command will now be available to you,
since you are in the virtual environment, your `PATH` environment was
updated to include a special version of ``python`` inside your ``.env``
folder with its own packages.

to test:

.. code-block:: bash

    $ ./run_tests.py

You probably didn't see anything but tests scroll by.

If you found a problem or are trying to write a test, you can file an
`issue on github`_.

.. _issue on github: https://github.com/tony/tmuxp/issues

.. _test_builder_visually:

Watch tmux testsuite build sessions visually
""""""""""""""""""""""""""""""""""""""""""""

The builder functionality of tmuxp, creates sessions, panes and windows
from a configuration. It's preferential to watch this from another
terminal.

Create two terminals:

  - Terminal 1: ``$ tmux -L test_case``
  - Terminal 2: ``$ cd`` into the tmuxp project and into the
    ``virtualenv`` if you are using one, see details on installing the dev
    version of tmuxp above.

    Now, type ``$ python ./run_tests.py --visual``

Terminal 1 should have flickered and built the session before your eyes.
tmuxp hides this building from normal users. :)

Re-run tests automatically on file edit
"""""""""""""""""""""""""""""""""""""""

.. note::
    This requires and installation of `node`_ and `npm`_ on your system!

    be sure your in the tmuxp project and virtualenv as discussed in
    :ref:`install_dev_env` (``source .env/bin/activate``).

Install `nodemon`_:

.. code-block:: bash

    $ sudo npm install -g nodemon

To run all tests upon editing any ``.py`` file:

.. code-block:: bash

    $ nodemon -e py --exec 'python' ./run_tests.py

To run test where :ref:`test_builder_visually` you may:

.. code-block:: bash

    $ nodemon -e py --exec 'python' ./run_tests.py --visual

.. _node: http://www.nodejs.org
.. _npm: http://www.npmjs.org
.. _nodemon: https://github.com/remy/nodemon


Deeper
""""""

You won't see anything since the tests are verified by status checking
commands, i.e.: ``list-sessions``, ``list-windows``, ``list-panes``.

Travis
""""""

Currently `travis-ci`_ is used to automate unit testing.


.. _travis-ci: http://www.travis-ci.org
