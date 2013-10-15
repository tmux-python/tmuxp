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

Our tests are inside ``./tmuxp/testsuite``. Tests are implemented using
:py:mod:`unittest`.

``./run_tests.py`` will create a tmux server on a separate ``socket_name``
using ``$ tmux -L test_case``.

.. _install_dev_env:

Install the latest code
-----------------------

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

run_tests.py
------------

As you seen above, the ``tmuxp`` command will now be available to you,
since you are in the virtual environment, your `PATH` environment was
updated to include a special version of ``python`` inside your ``.env``
folder with its own packages.

.. code-block:: bash

    $ ./run_tests.py

You probably didn't see anything but tests scroll by.

If you found a problem or are trying to write a test, you can file an
`issue on github`_.

.. _issue on github: https://github.com/tony/tmuxp/issues

.. _test_specific_tests:

Choose tests to run
"""""""""""""""""""

Testing specific testsuites, testcase and tests

.. code-block:: bash

    $ ./run_tests.py --help

Will give you an output of ways you can choose to run tests. Example for
``test_config`` TestSuite:

By :py:class:`unittest.TestSuite` / module:

.. code-block:: bash

    $ ./run_tests.py tmuxp.testsuite.test_config

by :py:class:`unittest.TestCase`:

.. code-block:: bash

    $ ./run_tests.py --tests tmuxp.testsuite.test_config.ImportExportTest

individual tests:

.. code-block:: bash

    $ ./run_tests.py --tests tmuxp.testsuite.test_config.ImportExportTest.test_export_json

Multiple can be separated by spaces:

.. code-block:: bash

    $ ./run_tests.py --tests tmuxp.testsuite.test_config.ImportExportTest.test_export_json \
        testsuite.test_config.ImportExportTest.test_window

.. _test_builder_visually:

Visual testing
""""""""""""""

You can watch tmux testsuite build sessions visually also.

Create two terminals:

  - Terminal 1: ``$ tmux -L test_case``
  - Terminal 2: ``$ cd`` into the tmuxp project and into the
    ``virtualenv`` if you are using one, see details on installing the dev
    version of tmuxp above. Then:

    .. code-block:: bash
    
        $ python ./run_tests.py --visual

Terminal 1 should have flickered and built the session before your eyes.
tmuxp hides this building from normal users. :)

Verbosity and logging
"""""""""""""""""""""

``./run_tests.py`` supports two options, these are *optional* flags that
may be added to for :ref:`test_specific_tests` and
:ref:`test_builder_visually`.

1.  log level: ``-l`` aka ``--log-level``, with the options of ``debug``,
    ``info``, ``warn``, ``error``, ``fatal``. Default is ``INFO``.

    .. code-block:: bash

        $ ./run_tests.py --log-level debug

    short form:

    .. code-block:: bash

        $ ./run_tests.py -l debug

2.  unit test verbosity:

    ``--verbosity`` may be set to ``0``, ``1`` and ``2``.  Default: ``2``.

    .. code-block:: bash

        $ ./run_tests.py --verbosity 0

Watch files and test
--------------------

You can re-run tests automatically on file edit.

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

Travis CI
---------

tmuxp uses `travis-ci`_ for continuous integration / automatic unit
testing.

travis allows for testing against multiple scenarios. Currently tmuxp
is tested against 1.8 and latest in addition to python 2.7. The
`travis build site`_ uses this `.travis.yml`_ configuration:

.. literalinclude:: ../.travis.yml
    :language: yaml

Internals
=========


Similarities to Tmux and Pythonics
----------------------------------

tmuxp is was built in the spirit of understanding how tmux operates
and how python objects and tools can abstract the API's in a pleasant way.

tmuxp uses the identify ``FORMATTERS`` used by tmux, you can see
them inside of http://sourceforge.net/p/tmux/tmux-code/ci/master/tree/format.c.

In this, I will also begin documenting the API.

the use of:

Session
Session.new_window() - returns a new Window object bound to the session,
also uses ``tmux new-window``.
Session.new_session() - class method - returns a new Session object.

Differences from tmux
---------------------

Because this is a python abstraction and flags like ``start-directory``
have dashes (-) replaced with underscores (_).

interesting observations
------------------------

How is tmuxp able to keep references to panes, windows and sessions?

    Tmux has unique ID's for sessions, windows and panes.

    panes use ``%``, such as ``%1234``

    windows use ``@``, such as ``@2345``

    sessions use ``$``, for money, such as ``$``

How is tmuxp able to handle windows with no names?

    Tmux provides ``window_id`` as a unique identifier.

What is a {pane,window}_index vs a {pane,window,session}_id?

    Pane index refers to the order of a pane on the screen.

    Window index refers to the # of the pane in the session.

How tmuxp verifies state
------------------------

How does tmuxp verify session / window / pane state?

Normal tests won't even require a tmux session being open already. Tests 
assert against the freshest data, ie: :meth:`tmuxp.Server.list_sessions`,
:meth:`tmuxp.Session.list_windows`, :meth:`tmuxp.Window.list_panes`.

Reference
---------

- tmux docs http://www.openbsd.org/cgi-bin/man.cgi?query=tmux&sektion=1
- tmux source code http://sourceforge.net/p/tmux/tmux-code/ci/master/tree/

.. _travis-ci: http://www.travis-ci.org
.. _travis build site: http://www.travis-ci.org/tony/tmuxp
.. _.travis.yml: https://github.com/tony/tmuxp/blob/master/.travis.yml
