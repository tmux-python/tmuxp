.. _api:

===
API
===

.. module:: tmuxp

Server Object
-------------

.. autoclass:: Server
   :members:
   :inherited-members:

   .. attribute:: _sessions

      A :py:obj:`list` of the server's :class:`Session` objects.

Session Object
--------------

.. autoclass:: Session
   :members:
   :inherited-members:
   :show-inheritance:

   .. attribute:: _windows

      A :py:obj:`list` of session's :class:`Window` objects.


Window Object
-------------

.. autoclass:: Window
   :members:
   :inherited-members:
   :show-inheritance:

   .. attribute:: _session

      The :class:`Session` of the window.

   .. attribute:: _panes

      A :py:obj:`list` of the window's :class:`Pane` objects.

Pane Object
-----------

.. autoclass:: Pane
   :members:
   :inherited-members:
   :show-inheritance:

   .. attribute:: _session

      The :class:`Session` of the pane.

   .. attribute:: _window

      The :class:`Window` of the pane.

Internals
---------

.. autoclass:: tmuxp.util.TmuxObject

.. autoclass:: tmuxp.util.tmux

Command Line
------------

.. automethod:: tmuxp.cli.startup

Configuration
-------------

Finding
"""""""

.. automethod:: tmuxp.config.is_config_file

.. automethod:: tmuxp.config.in_dir

.. automethod:: tmuxp.config.in_cwd

Import and export
"""""""""""""""""

.. automethod:: tmuxp.config.expand

.. automethod:: tmuxp.config.inline

.. automethod:: tmuxp.config.trickle

Workspace Builder
-----------------

.. autoclass:: tmuxp.WorkspaceBuilder
   :members:

Exceptions
----------

.. autoexception:: tmuxp.exc.TmuxSessionNotFound
.. autoexception:: tmuxp.exc.TmuxSessionExists
.. autoexception:: tmuxp.exc.TmuxNotRunning
