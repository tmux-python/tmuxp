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

    $ tmux new-session -n tmuxp_wins -s a_tmuxp_session

Why not just ``$ tmux``? We will assume you want to see the tmux changes
in the current tmux session. So we will use:

Window name: ``tmuxp_wins``
Session name: ``a_tmuxp_session``

We are inside of a tmux session, let's launch our python interpretter
(``$ python``, ``$ bpython`` or ``$ ipython``) and begin issuing commands
to tmuxp CLI style. For this I'll use ``python``.

.. code-block:: bash

    $ python

.. module:: tmuxp

First, we can grab a :class:`Server`.


.. code-block:: python

    server = tmuxp.Server()
    >>> server
    <tmuxp.server.Server object at 0x7fbd622c1dd0>


.. note::

    You can specify a ``socket_name``, ``socket_path`` and ``config_file``
    in your server object.  ``tmuxp.Server(socket_name='mysocket')`` is
    equivalent to ``$ tmux -L mysocket``.

``server`` is now a living object bound to the tmux server's Sessions,
Windows and Panes.

Find your :class:`Session`
--------------------------

.. todo::
    Update API to catch the ENV variables for the current ``TMUX`` socket,
    and allow a quick option to grab the current tmux's environment's
    :class:`Server`, :class:`Window` and :class:`Pane` via CLI.

If you have multiple tmux session's open. You can see that all of the
methods in :class:`Server` are available.

We can list sessions with :meth:`Server.list_sessions`:

.. code-block:: python

    >>> server.list_sessions()
    [Session($3 a_tmuxp_session), Session($1 tmuxp)]

This returns a list of :class:`Session` objects you can grab. You could
our current session with:

.. code-block:: python

    >>> server.list_sessions()[0]

That's not guaranteed. tmuxp works against current tmux information, the
session's name could be changed, or another tmux session may be created, 
so :meth:`Server.getById` and :meth:`Server.findWhere` exists as a lookup:

Get session by ID
-----------------

tmux sessions use the ``$[0-9]`` convention as a way to identify sessions.

``$3`` is whatever the ID ``list_sessions()`` returned above.

.. code-block::  python


    >>> server.getById('$3')
    Session($3 a_tmuxp_session)

You may ``session = getById('$<yourId>')`` to use the session object.

Get session by nane / other properties
--------------------------------------

I really like `Backbone`_'s approach to handling collections of structured
data. So I made a :meth:`Server.findWhere` method modelled after
`Backbone.Collection.prototype.findWhere`_.

.. code-block:: python

    >>> server.findWhere({ "session_name": "a_tmuxp_session" })
    Session($3 a_tmuxp_session)

With ``findWhere``, pass in a dict and return the first object found. In
this case, a :class:`Server` holds a collection of child :class:`Session`.
:class:`Session` and :class:`Window` both utilize ``findWhere`` to sift
through Windows and Panes, respectively.

So you may now use:

.. code-block:: python

    >>> session = server.findWhere({ "session_name": "a_tmuxp_session" })

to give us a ``session`` object to play with.

Playing with our tmux session
-----------------------------

.. todo::

  Consider migrating tmuxp to use a ``.execute`` sqlalchemy style and have
  commands such as ``new_window()`` return CLI output. Also tmuxp could use
  use "engine" as a way to control if it's using socket's or shell commands
  to handle tmux.

We now have access to ``session`` from above with all of the methods
available in :class:`Session`.

Let's make a :meth:`Session.new_window`, in the background:

.. code-block:: python

    >>> session.new_window(attach=False, window_name="ha in the bg")
    Window(@8 2:ha in the bg, Session($3 a_tmuxp_session))

So a few things:

1. ``attach=False`` meant to create a new window, but not to switch to it.
   It is the same as ``$ tmux new-window -d``.
2. ``window_name`` may be specified.
3. Returns the :class:`Window` object created.

.. note::

    In any of the cases, you can look up the detailed :ref:`api` to see all
    the options you have.

Let's delete that window (:meth:`Session.kill_window`).

Method 1: Use passthrough to tmux's ``target`` system.

.. code-block:: python

    >>> session.kill_window("ha in")

.. code-block::

.. _sliderepl: http://discorporate.us/projects/sliderepl/
.. _backbone: http:/ /backbonejs.org
.. _Backbone.Collection.prototype.findWhere: http://backbonejs.org/#Collection-findWhere
