.. module:: tmuxp

.. _developing:

======================
Developing and Testing
======================

.. todo::
    link to sliderepl or ipython notebook slides

Our tests are inside ``./tmuxp/testsuite``. Tests are implemented using
:py:mod:`unittest`.

``./run-tests.py`` will create a tmux server on a separate ``socket_name``
using ``$ tmux -L test_case``.

.. _install_dev_env:

Install the latest code from git
--------------------------------

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

Test Runner
-----------

As you seen above, the ``tmuxp`` command will now be available to you,
since you are in the virtual environment, your `PATH` environment was
updated to include a special version of ``python`` inside your ``.env``
folder with its own packages.

.. code-block:: bash

    $ ./run-tests.py

You probably didn't see anything but tests scroll by.

If you found a problem or are trying to write a test, you can file an
`issue on github`_.

.. _test_specific_tests:

Test runner options
"""""""""""""""""""

.. note::

    As of v0.0.20, ``--tests`` automatically assume the namespace of
    ``tmuxp.testsuite``.

    .. code-block:: bash

        $ ./run-tests.py --tests test_config.ImportExportTest

    Is now equivalent to:

    .. code-block:: bash

        $ ./run-tests.py --tests tmuxp.testsuite.test_config.ImportExportTest

Testing specific TestSuites, TestCase and tests

.. code-block:: bash

    $ ./run-tests.py --help

Will give you an output of ways you can choose to run tests. Example for
``test_config`` TestSuite:

By :py:class:`unittest.TestSuite` / module:

.. code-block:: bash

    $ ./run-tests.py test_config

by :py:class:`unittest.TestCase`:

.. code-block:: bash

    $ ./run-tests.py --tests test_config.ImportExportTest

individual tests:

.. code-block:: bash

    $ ./run-tests.py --tests test_config.ImportExportTest.test_export_json

Multiple can be separated by spaces:

.. code-block:: bash

    $ ./run-tests.py --tests ImportExportTest.test_export_json \
        ImportExportTest.test_window

.. _test_builder_visually:

Visual testing
''''''''''''''

You can watch tmux testsuite build sessions visually by keeping a client
open in a separate terminal.

Create two terminals:

  - Terminal 1: ``$ tmux -L test_case``
  - Terminal 2: ``$ cd`` into the tmuxp project and into the
    ``virtualenv`` if you are using one, see details on installing the dev
    version of tmuxp above. Then:

    .. code-block:: bash
    
        $ python ./run-tests.py --tests tests_workspacebuilder

Terminal 1 should have flickered and built the session before your eyes.
tmuxp hides this building from normal users.

Verbosity and logging
'''''''''''''''''''''

``./run-tests.py`` supports two options, these are *optional* flags that
may be added to for :ref:`test_specific_tests` and
:ref:`test_builder_visually`.

1.  log level: ``-l`` aka ``--log-level``, with the options of ``debug``,
    ``info``, ``warn``, ``error``, ``fatal``. Default is ``INFO``.

    .. code-block:: bash

        $ ./run-tests.py --log-level debug

    short form:

    .. code-block:: bash

        $ ./run-tests.py -l debug

2.  unit test verbosity:

    ``--verbosity`` may be set to ``0``, ``1`` and ``2``.  Default: ``2``.

    .. code-block:: bash

        $ ./run-tests.py --verbosity 0

Run tests on save
-----------------

You can re-run tests automatically on file edit.

.. note::
    This requires and installation of ``watching_testrunner`` from pypi.

Install `watching_testrunner`_ from `pypi`_:

.. code-block:: bash

    $ pip install watching_testrunner

To run all tests upon editing any ``.py`` file:

.. code-block:: bash

    $ watching_testrunner --basepath ./ --pattern="*.py" python run-tests.py

To run test where :ref:`test_builder_visually` you may:

.. code-block:: bash

    $ watching_testrunner --basepath ./ --pattern="*.py" python run-tests.py --visual

.. _watching_testrunner: https://pypi.python.org/pypi/watching_testrunner/1.0
.. _pypi: https://pypi.python.org/pypi

.. _tmuxp developer config:

tmuxp developer config
""""""""""""""""""""""

.. image:: _static/tmuxp-dev-screenshot.png
    :scale: 100%
    :width: 60%
    :align: center

After you :ref:`install_dev_env`, when inside the tmuxp checkout:

.. code-block:: bash

    $ tmuxp load .

this will load the ``.tmuxp.yaml`` in the root of the project.

.. literalinclude:: ../.tmuxp.yaml
    :language: yaml

.. _travis:

Travis CI
"""""""""

tmuxp uses `travis-ci`_ for continuous integration / automatic unit
testing.

tmuxp is tested against tmux 1.8 and the latest git source. Interpretters
tested are 2.6, 2.7 and 3.3. The `travis build site`_ uses this
`.travis.yml`_ configuration:

.. literalinclude:: ../.travis.yml
    :language: yaml

.. _travis-ci: http://www.travis-ci.org
.. _travis build site: http://www.travis-ci.org/tony/tmuxp
.. _.travis.yml: https://github.com/tony/tmuxp/blob/master/.travis.yml
.. _issue on github: https://github.com/tony/tmuxp/issues
