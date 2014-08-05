.. _Internals:

=========
Internals
=========

.. seealso:: :ref:`api`

.. module:: tmuxp

tmuxp is an *abstraction layer* against tmux' command line arguments.

:class:`util.TmuxRelationalObject` acts as a container to connect the
relations of :class:`Server`, :class:`Session`, :class:`Window` and
:class:`Pane`.

======================== ======================= =========================
Object                   Child                   Parent
======================== ======================= =========================
:class:`Server`          :class:`Session`        None
:class:`Session`         :class:`Window`         :class:`Server`
:class:`Window`          :class:`Pane`           :class:`Session`
:class:`Pane`            None                    :class:`Window`
======================== ======================= =========================

Internally, tmux allows multiple servers to be ran on a system. Each one
uses a socket. Most users worry since tmux will communicate to a default
server automatically. If one doesn't exist, tmux does it for you.

A server can have multiple sessions. ``Ctrl-a s`` can be used to switch
between sessions running on the server.

Sessions, Windows and Panes all have their own unique identifier for
internal purposes. :class:`util.TmuxMappingObject` will make use of the
unique identifiers (``session_id``, ``window_id``, ``pane_id`` ) to look
up the data stored in the :class:`Server` object.

======================== ======================= =========================
Object                   Prefix                  Example
======================== ======================= =========================
:class:`Server`          N/A                     N/A, uses ``socket-name``
                                                 and ``socket-path``
:class:`Session`         ``$``                   ``$13``
:class:`Window`          ``@``                   ``@3243``           
:class:`Pane`            ``%``                   ``%5433``
======================== ======================= =========================

Similarities to Tmux and Pythonics
----------------------------------

tmuxp is was built in the spirit of understanding how tmux operates
and how python objects and tools can abstract the API's in a pleasant way.

tmuxp uses ``FORMATTERS`` in tmux to give identity attributes to
:class:`Session`, :class:`Window` and :class:`Pane` objects. See
`formatters.c`_.

.. _formatters.c: http://sourceforge.net/p/tmux/tmux-code/ci/master/tree/format.c

How is tmuxp able to keep references to panes, windows and sessions?

    Tmux has unique ID's for sessions, windows and panes.

    panes use ``%``, such as ``%1234``

    windows use ``@``, such as ``@2345``

    sessions use ``$``, for money, such as ``$``

How is tmuxp able to handle windows with no names?

    Tmux provides ``window_id`` as a unique identifier.

What is a {pane,window}_index vs a {pane,window,session}_id?

    Pane index refers to the order of a pane on the screen.

    Window index refers to the # of the window in the session.

To assert pane, window and session data, tmuxp will use
:meth:`Server.list_sessions()`, :meth:`Session.list_windows()`,
:meth:`Window.list_panes()` to update objects.

Idiosyncrasies
--------------

Because this is a python abstraction and commands like ``new-window``
have dashes (-) replaced with underscores (_).

Reference
---------

- tmux docs http://www.openbsd.org/cgi-bin/man.cgi?query=tmux&sektion=1
- tmux source code http://sourceforge.net/p/tmux/tmux-code/ci/master/tree/

.. _abstraction layer: http://en.wikipedia.org/wiki/Abstraction_layer
.. _ORM: http://en.wikipedia.org/wiki/Object-relational_mapping
