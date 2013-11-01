.. _api:

====================
Python API Reference
====================

.. module:: tmuxp

Server Object
-------------

.. autoclass:: Server
    :members:
    :inherited-members:
    :private-members:
    :show-inheritance:
    :member-order: bysource

Session Object
--------------

.. autoclass:: Session
    :members:
    :inherited-members:
    :show-inheritance:

    .. attribute:: server

        The :class:`Server` of the window.

    .. attribute:: windows

        A :py:obj:`list` of the window's :class:`Window` objects.

    .. attribute:: _window

        A :py:obj:`list` of the session's windows as :py:obj:`dict`.

Window Object
-------------

.. autoclass:: Window
    :members:
    :inherited-members:
    :private-members:
    :show-inheritance:

    .. attribute:: session

        The :class:`Session` of the window.

    .. attribute:: panes

        A :py:obj:`list` of the window's :class:`Pane` objects.

    .. attribute:: _panes

        A :py:obj:`list` of the window's panes as :py:obj:`dict`.

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

.. autoclass:: tmuxp.util.TmuxRelationalObject
    :members:

.. autoclass:: tmuxp.util.TmuxMappingObject
    :members:

.. autoclass:: tmuxp.util.tmux

.. automethod:: tmuxp.util.version

.. automethod:: tmuxp.util.oh_my_zsh_auto_title

.. automethod:: tmuxp.util.which

Command Line
------------

.. automethod:: tmuxp.cli.startup

.. automethod:: tmuxp.cli.prompt
.. automethod:: tmuxp.cli.prompt_bool
.. automethod:: tmuxp.cli.prompt_choices

.. automethod:: tmuxp.cli.setup_logger
.. automethod:: tmuxp.cli.get_parser

Configuration
-------------

Finding
"""""""

.. automethod:: tmuxp.config.is_config_file

.. automethod:: tmuxp.config.in_dir

.. automethod:: tmuxp.config.in_cwd

Import and export
"""""""""""""""""

.. automethod:: tmuxp.config.check_consistency

.. automethod:: tmuxp.config.expand

.. automethod:: tmuxp.config.inline

.. automethod:: tmuxp.config.trickle

.. automethod:: tmuxp.config.import_teamocil

.. automethod:: tmuxp.config.import_tmuxinator

Workspace Builder
-----------------

.. autoclass:: tmuxp.WorkspaceBuilder
   :members:

Exceptions
----------

.. autoexception:: tmuxp.exc.TmuxSessionExists

.. autoexception:: tmuxp.exc.EmptyConfigException

.. autoexception:: tmuxp.exc.ConfigError


