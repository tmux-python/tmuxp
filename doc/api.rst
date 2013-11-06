.. _api:

=============
API Reference
=============

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
    :private-members:
    :show-inheritance:
    :member-order: bysource

Window Object
-------------

.. autoclass:: Window
    :members:
    :inherited-members:
    :private-members:
    :show-inheritance:
    :member-order: bysource

Pane Object
-----------

.. autoclass:: Pane
    :members:
    :inherited-members:
    :private-members:
    :show-inheritance:
    :member-order: bysource

Internals
---------

.. autoclass:: tmuxp.util.TmuxRelationalObject
    :members:

.. autoclass:: tmuxp.util.TmuxMappingObject
    :members:

.. autoclass:: tmuxp.util.tmux

.. automethod:: tmuxp.util.has_required_tmux_version

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

.. automethod:: tmuxp.cli.load_workspace

Configuration
-------------

Finding
"""""""

.. automethod:: tmuxp.config.is_config_file

.. automethod:: tmuxp.config.in_dir

.. automethod:: tmuxp.config.in_cwd

Import and export
"""""""""""""""""

.. automethod:: tmuxp.config.validate_schema

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

.. autoexception:: tmuxp.exc.TmuxpException

.. autoexception:: tmuxp.exc.TmuxSessionExists

.. autoexception:: tmuxp.exc.EmptyConfigException

.. autoexception:: tmuxp.exc.ConfigError


