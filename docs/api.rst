.. _api:

=============
API Reference
=============

.. seealso::
    See :ref:`libtmux's API <libtmux:api>` and :ref:`Quickstart
    <libtmux:quickstart>` to see how you can control tmux via python API calls.

.. module:: tmuxp

Internals
---------

.. automethod:: tmuxp.util.run_before_script

.. automethod:: tmuxp.util.oh_my_zsh_auto_title

.. automethod:: tmuxp.util.raise_if_tmux_not_running

.. automethod:: tmuxp.util.get_current_pane

.. automethod:: tmuxp.util.get_session

.. automethod:: tmuxp.util.get_window

.. automethod:: tmuxp.util.get_pane

CLI
---

.. automethod:: tmuxp.cli._reattach
.. automethod:: tmuxp.cli.get_config_dir
.. automethod:: tmuxp.cli.get_teamocil_dir
.. automethod:: tmuxp.cli.get_tmuxinator_dir
.. automethod:: tmuxp.cli.load_workspace
.. automethod:: tmuxp.cli._validate_choices

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

.. automethod:: tmuxp.config.expandshell

.. automethod:: tmuxp.config.expand

.. automethod:: tmuxp.config.inline

.. automethod:: tmuxp.config.trickle

.. automethod:: tmuxp.config.import_teamocil

.. automethod:: tmuxp.config.import_tmuxinator

Workspace Builder
-----------------

.. autoclass:: tmuxp.workspacebuilder.WorkspaceBuilder
   :members:

.. automethod:: tmuxp.workspacebuilder.freeze

Exceptions
----------

.. autoexception:: tmuxp.exc.EmptyConfigException

.. autoexception:: tmuxp.exc.ConfigError

.. autoexception:: tmuxp.exc.BeforeLoadScriptError

.. autoexception:: tmuxp.exc.BeforeLoadScriptNotExists
