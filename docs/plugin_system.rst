.. _plugin_system:

=============
Plugin System
=============

The plugin system allows users to customize and extend different aspects of 
tmuxp without the need to change tmuxp itself. 


Using a Plugin
--------------

To use a plugin, install it in your local python environment and add it to 
your tmuxp configuration file. 

Example Configurations
^^^^^^^^^^^^^^^^^^^^^^
YAML
~~~~

.. literalinclude:: ../examples/plugin-system.yaml
    :language: yaml

JSON
~~~~

.. literalinclude:: ../examples/plugin-system.json
    :language: json

.. _poetry: https://python-poetry.org/


Developing a Plugin
-------------------

.. module:: tmuxp 

Plugin API
^^^^^^^^^^

.. automethod:: tmuxp.plugin.TmuxpPluginInterface.before_workspace_builder
.. automethod:: tmuxp.plugin.TmuxpPluginInterface.on_window_create
.. automethod:: tmuxp.plugin.TmuxpPluginInterface.after_window_finished
.. automethod:: tmuxp.plugin.TmuxpPluginInterface.before_script
.. automethod:: tmuxp.plugin.TmuxpPluginInterface.reattach


Example Plugin
--------------

Tmuxp expects all plugins to be class within a python submodule named 
``plugin`` that is within a python module that is installed in the local 
python environment. A plugin interface is provided by tmuxp to inherit. 

`poetry`_ is the chosen python package manager for tmuxp. It is highly 
suggested to use it when developing tmuxp plugins; however, ``pip`` will work 
just as well.

.. code-block:: bash

    python_module
    ├── my_plugin_module
    │   ├── __init__.py
    │   └── plugin.py
    ├── pyproject.toml  # Poetry's module configuration file
    └── setup.py        # pip's module configuration file

The `plugin.py` file could contain something like the following:

.. code-block:: python
    
    from tmuxp.plugin import TmuxpPluginInterface
    import datetime

    class MyTmuxpPlugin(TmuxpPluginInterface):
        def __init__(self):
            super.__init__(self)

        def before_workspace_builder(self, session):
            session.rename_session('my-new-session-name')

        def reattach(self, session):
            now = datetime.datetime.now().strftime('%Y-%m-%d')
            session.rename_session('session_{}'.format(now))

Once this plugin is installed in the local python environment, it can be used
in a configuration file like the following:

.. code-block: yaml

    session_name: plugin example
    plugins:
    - my_plugin_module.plugin.MyTmuxpPlugin
    # ... the rest of your config
