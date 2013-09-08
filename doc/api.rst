.. _api:

API
===

.. module:: tmuxp

tmuxp api

Server Object
-------------

.. autoclass:: Server
   :members:
   :inherited-members:
   :show-inheritance:

   .. attribute:: _sessions

      A :py:class:`list` of all the :class:`Session` objects in the server.

Session Object
--------------

.. autoclass:: Session
   :members:
   :inherited-members:
   :show-inheritance:

   .. attribute:: _windows

      A :python:`list` of all the :class:`Window` objects in the server.


Window Object
-------------

.. autoclass:: Window
   :members:
   :inherited-members:
   :show-inheritance:

   .. attribute:: _session

      The :class:`Session` of the window.

   .. attribute:: _windows

      A :py:class:`list` of all the :class:`Pane` objects in the server.

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
   :show-inheritance:

.. automethod:: tmuxp.util.tmux

.. automethod:: tmuxp.util.live_tmux

Configuration
-------------

.. autoclass:: tmuxp.util.ConfigExpand

.. autoclass:: tmuxp.util.ConfigTrickleDown

