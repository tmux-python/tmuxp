.. _python_api_quickstart:

=====================
Python API Quickstart
=====================

tmuxp allows for developers and system administrators to control live tmux
sessions using python code.

In this example, we will launch a tmux session and control the windows
from inside a live tmux session.


Setting up tab-completion
-------------------------

To begin, it's preferable to install a python CLI with tab-completion.

You can install a custom python shell like `bpython`_ or `iPython`_, which
has some awesome CLI features, or setup vanilla :py:mod:`readline` support.

``readline`` tab-completion
"""""""""""""""""""""""""""

.. seealso::
    Source: `How do I add tab-completion to the python shell`_ on 
    `StackOverflow`_.

Create ``~.pythonrc`` in ``$HOME`` folder:

.. code-block:: python

    # ~/.pythonrc
    # enable syntax completion
    try:
        import readline
    except ImportError:
        print "Module readline not available."
    else:
        import rlcompleter
        readline.parse_and_bind("tab: complete")

Then to your ``.bashrc`` or ``.zshrc`` file, add:

.. code-block:: bash

    export PYTHONSTARTUP=~/.pythonrc

.. _How do I add tab-completion to the python shell: http://stackoverflow.com/a/246779
.. _StackOverflow: http://www.stackoverflow.com

bpython or ipython cli
""""""""""""""""""""""

`bpython`_ can be installed with ``$ [sudo] pip install bpython`` and
`ipython`_ can be installed with ``$ [sudo] pip install ipython``.

bpython allows using ``<F2>`` to see the source of CLI methods in colors.

.. todo::
    If you know any extra benefits of ipython or bpython for CLI and could
    list them here please edit this page.


.. _bpython: https://bitbucket.org/bobf/bpython
.. _ipython: http://ipython.org

Control tmux via python
-----------------------

.. seealso:: :ref:`api`

.. todo:: Do a version of this with `sliderepl`_

To begin, ensure  the ``tmux`` program is installed.

Next, ensure ``tmuxp`` (note the p!) is installed:

.. code-block:: bash

    $ [sudo] pip install tmuxp

Now, let's open a tmux session.

.. code-block:: bash

    $ tmux

We are inside of a tmux session, let's launch our python interpretter
(``$ python``, ``$ bpython`` or ``$ ipython``) and begin issuing commands
to tmuxp CLI style. For this I'll use ``python``.

.. code-block:: bash

    $ python

.. module:: tmuxp

First, we can grab a :class:`Server`.


.. code-block:: python

    server = tmuxp.Server()

.. note::

    You can specify a ``socket_name``, ``socket_path`` and ``config_file``
    in your server object.  ``tmuxp.Server(socket_name='mysocket')`` is
    equivalent to ``$ tmux -L mysocket``.

``server`` is now a living object bound to the tmux server's Sessions,
Windows and Panes.


.. _sliderepl: http://discorporate.us/projects/sliderepl/
