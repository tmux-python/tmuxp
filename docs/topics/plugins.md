(plugins)=

# Plugins

The plugin system allows users to customize and extend different aspects of
tmuxp without the need to change tmuxp itself.

## Using a Plugin

To use a plugin, install it in your local python environment and add it to
your tmuxp workspace file.

### Example Workspace files

````{tab} YAML

```{literalinclude} ../../examples/plugin-system.yaml
:language: yaml

```

````

````{tab} JSON

```{literalinclude} ../../examples/plugin-system.json
:language: json

```

````

## Developing a Plugin

tmuxp expects all plugins to be a class within a python submodule named
`plugin` that is within a python module that is installed in the local
python environment. A plugin interface is provided by tmuxp to inherit.

[uv] is the chosen python package manager for tmuxp. It is highly
suggested to use it when developing plugins; however, `pip` will work
just as well. Only one of the configuration files is needed for the packaging
tool that the package developer decides to use.

```console

python_module
├── tmuxp_plugin_my_plugin_module
│   ├── __init__.py
│   └── plugin.py
└── pyproject.toml  # Python project configuration file

```

When publishing plugins to pypi, tmuxp advocates for standardized naming:
`tmuxp-plugin-{your-plugin-name}` to allow for easier searching. To create a
module configuration file with uv, run `uv virtualenv` in the module
directory. The resulting file looks something like this:

```toml

[project]
name = "tmuxp-plugin-my-tmuxp-plugin"
version = "0.0.2"
description = "An example tmuxp plugin."
authors = ["Author Name <author.name@<domain>.com>"]
requires-python = ">=3.8,<4.0"
dependencies = [
  "tmuxp^=1.7.0"
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

The `plugin.py` file could contain something like the following:

```python

from tmuxp.plugin import TmuxpPlugin
import datetime

class MyTmuxpPlugin(TmuxpPlugin):
    def __init__(self):
        """
        Initialize my custom plugin.
        """
        # Optional version dependency configuration. See Plugin API docs
        # for all supported config parameters
        config = {
            'tmuxp_min_version' = '1.6.2'
        }

        TmuxpPlugin.__init__(
            self,
            plugin_name='tmuxp-plugin-my-tmuxp-plugin',
            **config
        )

    def before_workspace_builder(self, session):
        session.rename_session('my-new-session-name')

    def reattach(self, session):
        now = datetime.datetime.now().strftime('%Y-%m-%d')
        session.rename_session('session_{}'.format(now))

```

Once this plugin is installed in the local python environment, it can be used
in a configuration file like the following:

```yaml
session_name: plugin example
plugins:
  - my_plugin_module.plugin.MyTmuxpPlugin
# ... the rest of your config
```

## Plugin API

```{eval-rst}
.. automethod:: tmuxp.plugin.TmuxpPlugin.__init__
```

```{eval-rst}
.. automethod:: tmuxp.plugin.TmuxpPlugin.before_workspace_builder
```

```{eval-rst}
.. automethod:: tmuxp.plugin.TmuxpPlugin.on_window_create
```

```{eval-rst}
.. automethod:: tmuxp.plugin.TmuxpPlugin.after_window_finished
```

```{eval-rst}
.. automethod:: tmuxp.plugin.TmuxpPlugin.before_script
```

```{eval-rst}
.. automethod:: tmuxp.plugin.TmuxpPlugin.reattach
```

[uv]: https://github.com/astral-sh/uv
