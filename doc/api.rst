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
