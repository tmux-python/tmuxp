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

Then in your ``.bashrc`` or ``.zshrc`` file, add:

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

    >>> import tmuxp
    >>> server = tmuxp.Server()
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

If you have multiple tmux sessions open, you can see that all of the
methods in :class:`Server` are available.

We can list sessions with :meth:`Server.list_sessions`:

.. code-block:: python

    >>> server.list_sessions()
    [Session($3 a_tmuxp_session), Session($1 tmuxp)]

This returns a list of :class:`Session` objects you can grab. We can
find our current session with:

.. code-block:: python

    >>> server.list_sessions()[0]

However, this isn't guaranteed, tmuxp works against current tmux information, the
session's name could be changed, or another tmux session may be created,
so :meth:`Server.getById` and :meth:`Server.findWhere` exists as a lookup.

Get session by ID
-----------------

tmux sessions use the ``$[0-9]`` convention as a way to identify sessions.

``$3`` is whatever the ID ``list_sessions()`` returned above.

.. code-block::  python


    >>> server.getById('$3')
    Session($3 a_tmuxp_session)

You may ``session = getById('$<yourId>')`` to use the session object.

Get session by name / other properties
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
  commands such as ``new_window()`` return CLI output. Also tmuxp could
  use "engine" as a way to control if it's using a socket or shell commands
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

The window in the bg dissappeared. This was the equivalent of ``$ tmux kill-window -t'ha in'``

Internally, tmux uses ``target``. Its specific behavior depends on what the target is, view the tmux manpage for more information.

    This section contains a list of the commands supported by tmux.  Most commands accept the optional -t argument with one of target-client, target-session target-window, or target-pane.

In this case, you can also go back in time and recreate the window again. The CLI should have history, so navigate up with the arrow key.

.. code-block:: python

    >>> session.new_window(attach=False, window_name="ha in the bg")
    Window(@11 3:ha in the bg, Session($3 a_tmuxp_session))

Try to kill the window by the matching id ``@[0-9999]``.

.. code-block:: python

    >>> session.new_window(attach=False, window_name="ha in the bg")
    Window(@12 3:ha in the bg, Session($3 a_tmuxp_session))


.. code-block:: python

    >>> session.kill_window('@12')

In addition, you could also ``.kill_window`` direction from the :class:`Window`
object:

.. code-block:: python

    >>> window = session.new_window(attach=False, window_name="check this out")

And kill:

.. code-block:: python

    >>> window.kill_window()

And of course, you can use :meth:`Session.list_windows()` and :meth:`Session.findWhere()`
to list and sort through active :class:`Window`'s.

Manipulating windows
--------------------

Now that we know how to create windows, let's use one. Let's use :meth:`Session.attached_window()`
to grab our current window.

.. code-block:: python

    >>> window = session.attached_window()

``window`` now has access to all of the objects inside of :class:`Window`.

Let's create a pane, :meth:`Window.split_window`:

.. code-block:: python

    >>> window.split_window(attach=False)
    Pane(%23 Window(@10 1:tmuxp_wins, Session($3 a_tmuxp_session)))

Powered up. Let's have a break down:

1. ``window = session.attached_window()`` gave us the :class:`Window` of the current attached to window.
2. ``attach=False`` assures the cursor didn't switch to the newly created pane.
3. Returned the created :class:`Pane`.

Also, since you are aware of this power, let's commemorate the experience:

.. code-block:: python

    >>> window.rename_window('tmuxpower')
    Window(@10 1:tmuxpower, Session($3 a_tmuxp_session))

You should have noticed :meth:`Window.rename_window` renamed the window.

Moving cursor across windows and panes
--------------------------------------

You have two ways you can move your cursor to new sessions, windows and panes.

For one, arguments such as ``attach=False`` can be omittted.

.. code-block:: python

    >>> pane = window.split_window()

This gives you the :class:`Pane` along with moving the cursor to a new window. You
can also use the ``.select_*`` available on the object, in this case the pane has
:meth:`Pane.select_pane()`.

.. code-block:: python

    >>> pane = window.split_window(attach=False)
    >>> pane.select_pane()

.. note:: There is much, much more. Take a look at the :ref:`API` and the `testsuite`_.

.. todo:: create a ``kill_pane()`` method.
.. todo:: have a ``.kill()`` and ``.select()`` proxy for Server, Session, Window and Pane objects.

Sending commands to tmux panes remotely
---------------------------------------

You may send commands to panes, windows and sessions **without** them being visible.
As long as you have the object, or are iterating through a list of them, you can use ``.send_keys``.

.. code-block:: python

    >>> window = session.new_window(attach=False, window_name="test")
    >>> pane = window.split_window(attach=False)
    >>> pane.send_keys('echo hey', enter=False)

See the other window, notice that :meth:`Pane.send_keys` has " ``echo hey``" written,
*still in the prompt*. Note the leading space character so the command won't be added to the user's history. Use `pane.cmd('send-keys', text)` to send keys without this leading space.

``enter=False`` can be used to send keys without pressing return. In this case,
you may leave it to the user to press return himself, or complete a command
using :meth:`Pane.enter()`:

.. code-block:: python

    >>> pane.enter()

Final notes
-----------

These objects created use tmux's internal usage of ID's to make servers,
sessions, windows and panes accessible at the object level.

You don't have to see the tmux session to be able to orchestrate it. After
all, :class:`WorkspaceBuilder` uses these same internals to build your
sessions in the background. :)

.. seealso::

    If you want to dig deeper, check out :ref:`API`, the code for
    `workspacebuilder.py`_ and our `testsuite`_ (see :ref:`developing`.)

.. _sliderepl: http://discorporate.us/projects/sliderepl/
.. _backbone: http:/ /backbonejs.org
.. _Backbone.Collection.prototype.findWhere: http://backbonejs.org/#Collection-findWhere
.. _workspacebuilder.py: https://github.com/tony/tmuxp/blob/master/tmuxp/workspacebuilder.py
.. _testsuite: https://github.com/tony/tmuxp/tree/master/tmuxp/testsuite
