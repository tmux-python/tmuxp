.. _quickstart:

==========
Quickstart
==========

Tmux Session Manager
--------------------

tmuxp can launch a tmux session from a configuration file.

Configuration files can be stored in ``$HOME/.tmuxp`` or in project
directories as ``.tmuxp.py``, ``.tmuxp.json`` or ``.tmuxp.yaml``.

Scripting
---------

Conventions
"""""""""""

.. module:: tmuxp

.. seealso:: :ref:`tmuxp python API documentation <api>`

======================================== =================================
:ref:`tmuxp python api <api>`            :term:`tmux(1)` equivalent
======================================== =================================
:class:`Server.list_sessions()`          ``$ tmux list-sessions``
:class:`Session.list_windows()`          ``$ tmux list-windows``
:class:`Window.list_panes()`             ``$ tmux list-panes``
:class:`Server.new_session()`            ``$ tmux new-session``
:class:`Session.new_window()`            ``$ tmux new-window``
:class:`Window.split_window()`           ``$ tmux split-window``
:class:`Pane.send_keys()`                ``$ tmux send-keys``
======================================== =================================

tmux ORM
""""""""

tmuxp's main internal feature is to abstract tmux into relational objects.

- :class:`Server` holds :class:`Session` objects.
- :class:`Session` holds :class:`Window` objects.
- :class:`Window` holds :class:`Pane` objects.
