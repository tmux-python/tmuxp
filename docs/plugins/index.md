(plugins)=

# Plugins

The plugin system allows users to customize and extend different aspects of
tmuxp without the need to change tmuxp itself.

## Using a Plugin

To use a plugin, install it in your local python environment and add it to
your tmuxp configuration file.

### Example Configurations

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

[poetry]: https://python-poetry.org/

## Developing a Plugin

tmuxp expects all plugins to be class within a python submodule named
`plugin` that is within a python module that is installed in the local
python environment. A plugin interface is provided by tmuxp to inherit.

[poetry][poetry] is the chosen python package manager for tmuxp. It is highly
suggested to use it when developing plugins; however, `pip` will work
just as well. Only one of the configuration files is needed for the packaging
tool that the package developer desides to use.

```console

python_module
├── tmuxp_plugin_my_plugin_module
│   ├── __init__.py
│   └── plugin.py
├── pyproject.toml  # Poetry's module configuration file
└── setup.py        # pip's module configuration file

```

When publishing plugins to pypi, tmuxp advocates for standardized naming:
`tmuxp-plugin-{your-plugin-name}` to allow for easier searching. To create a
module configuration file with poetry, run `poetry init` in the module
directory. The resulting file looks something like this:

```toml

[tool.poetry]
name = "tmuxp-plugin-my-tmuxp-plugin"
version = "0.0.2"
description = "An example tmuxp plugin."
authors = ["Author Name <author.name@<domain>.com>"]

[tool.poetry.dependencies]
python = "^3.6"
tmuxp = "^1.6.0"

[tool.poetry.dev-dependencies]

[build-system]
requires = ["poetry>=0.12"]
build-backend = "poetry.masonry.api"

```

The {}`plugin.py` file could contain something like the following:

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
