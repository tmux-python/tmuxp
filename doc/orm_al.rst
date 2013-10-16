.. _orm_al:

=========================
ORM and Abstraction Layer
=========================

.. module:: tmuxp

tmuxp is an `abstraction layer` against tmux' command line arguments.

tmuxp is an `ORM` in the sense bases of :class:`util.TmuxObject`, such as
:class:`Server`, :class:`Session`, :class:`Window` and :class:`Pane`
are stateful objects and related to their parent or child.

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
internal purposes.

======================== ======================= =========================
Object                   Prefix                  Example
======================== ======================= =========================
:class:`Server`          N/A                     N/A, uses ``socket-name``
                                                 and ``socket-path``
:class:`Session`         ``$``                   ``$13``
:class:`Window`          ``@``                   ``@3243``           
:class:`Pane`            ``%``                   ``%5433``
======================== ======================= =========================

.. _abstraction layer: http://en.wikipedia.org/wiki/Abstraction_layer
.. _ORM: http://en.wikipedia.org/wiki/Object-relational_mapping
