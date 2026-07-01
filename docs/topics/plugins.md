(plugins)=

# Plugins

Plugins let you customize and extend how tmuxp builds a session — renaming it,
reacting when you reattach, running setup at specific moments — without forking
tmuxp or hand-editing your workspace files. This is an advanced, opt-in feature:
most users never write or install one, and a workspace loads exactly the same
with no plugins at all. Reach for a plugin when you want behavior the workspace
format can't express and you're comfortable writing a little Python.

## Using a plugin

Install the plugin into the same Python environment as tmuxp, then name it in
your workspace file under `plugins`:

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

## When your hooks fire

A plugin is a class whose methods tmuxp calls at set points while it builds and
attaches the session. You override only the hooks you care about; the rest do
nothing. {ref}`tmuxp load <cli-load>` drives the lifecycle in a fixed order:

:::{mermaid}
:caption: When each plugin hook fires.

flowchart TD
    load["tmuxp load"]:::cmd --> bwb["before_workspace_builder"]:::cmd
    bwb --> oc["on_window_create"]:::cmd
    oc --> panes["create panes, run commands"]
    panes --> awf["after_window_finished"]:::cmd
    awf -->|more windows| oc
    awf -->|all windows built| bs["before_script"]:::cmd
    bs --> reattach["reattach"]:::cmd
:::

{meth}`~tmuxp.plugin.TmuxpPlugin.before_workspace_builder` runs first, once
the session exists but before any windows.
{meth}`~tmuxp.plugin.TmuxpPlugin.on_window_create` and
{meth}`~tmuxp.plugin.TmuxpPlugin.after_window_finished` bracket each window's
panes. Two of the names can mislead:
{meth}`~tmuxp.plugin.TmuxpPlugin.before_script` runs _after_ the whole session
is built — it augments, rather than replaces, the workspace's own
`before_script` — and {meth}`~tmuxp.plugin.TmuxpPlugin.reattach` fires only
when tmuxp re-attaches you to a session that already exists.

## Developing a plugin

tmuxp expects a plugin to be a class in a Python submodule named `plugin`, inside
a module installed in the same environment as tmuxp. You inherit from the
interface tmuxp provides, {class}`~tmuxp.plugin.TmuxpPlugin`.

[uv] is tmuxp's package manager of choice, and what these examples use; `pip`
works just as well. You need only one project file, for whichever packaging tool
you choose.

```console
python_module
├── tmuxp_plugin_my_plugin_module
│   ├── __init__.py
│   └── plugin.py
└── pyproject.toml  # Python project configuration file
```

When publishing to [PyPI], tmuxp suggests the naming convention
`tmuxp-plugin-{your-plugin-name}` so others can find it. A minimal
`pyproject.toml` looks like this:

```toml
[project]
name = "tmuxp-plugin-my-tmuxp-plugin"
version = "0.0.2"
description = "An example tmuxp plugin."
authors = [{ name = "Author Name", email = "author.name@example.com" }]
requires-python = ">=3.10"
dependencies = [
  "tmuxp>=1.7.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

The `plugin.py` file holds the class:

```python
import datetime

from tmuxp.plugin import TmuxpPlugin


class MyTmuxpPlugin(TmuxpPlugin):
    def __init__(self):
        """Initialize my custom plugin."""
        # Optional version-dependency configuration. See the Plugin API
        # docs for every supported parameter.
        config = {
            'tmuxp_min_version': '1.6.2',
        }

        TmuxpPlugin.__init__(
            self,
            plugin_name='tmuxp-plugin-my-tmuxp-plugin',
            **config,
        )

    def before_workspace_builder(self, session):
        session.rename_session('my-new-session-name')

    def reattach(self, session):
        now = datetime.datetime.now().strftime('%Y-%m-%d')
        session.rename_session('session_{}'.format(now))
```

Once it's installed in the same environment, name it in a workspace file:

```yaml
session_name: plugin example
plugins:
  - my_plugin_module.plugin.MyTmuxpPlugin
# ... the rest of your workspace
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
[PyPI]: https://pypi.org/
