.. _api:

=============
API Reference
=============

.. seealso::
    :ref:`python_api_quickstart` to see how you can control tmux via
    python API calls.

.. module:: tmuxp

Internals
---------

.. automethod:: tmuxp.util.run_before_script

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

.. automethod:: tmuxp.config.expandshell

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

.. autoexception:: tmuxp.exc.EmptyConfigException

.. autoexception:: tmuxp.exc.ConfigError

.. autoexception:: tmuxp.exc.BeforeLoadScriptError

.. autoexception:: tmuxp.exc.BeforeLoadScriptNotExists
