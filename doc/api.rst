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
   :show-inheritance:

.. automethod:: tmuxp.util.tmux

.. automethod:: tmuxp.util.live_tmux

Configuration
-------------

.. autoclass:: tmuxp.ConfigExpand
   :members:

.. autoclass:: tmuxp.ConfigTrickleDown
   :members:

Builder
-------

.. autoclass:: tmuxp.Builder
   :members:
