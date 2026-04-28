(index)=

# tmuxp

Session manager for tmux. Load, freeze, and convert tmux sessions through
YAML/JSON configuration files. Powered by [libtmux](https://libtmux.git-pull.com/).

::::{grid} 1 2 3 3
:gutter: 2 2 3 3

:::{grid-item-card} Quickstart
:link: quickstart
:link-type: doc
Install and run your first command.
:::

:::{grid-item-card} CLI Reference
:link: cli/index
:link-type: doc
Every command, flag, and option.
:::

:::{grid-item-card} Configuration
:link: configuration/index
:link-type: doc
Config format, examples, and environment variables.
:::

::::

::::{grid} 1 1 2 2
:gutter: 2 2 3 3

:::{grid-item-card} Topics
:link: topics/index
:link-type: doc
Workflows, plugins, and troubleshooting.
:::

:::{grid-item-card} Contributing
:link: project/index
:link-type: doc
Internals, development setup, and release process.
:::

::::

## Install

```console
$ pip install tmuxp
```

```console
$ uv tool install tmuxp
```

```console
$ brew install tmuxp
```

See [Quickstart](quickstart.md) for all installation methods and first steps.

## Load a workspace

```yaml
session_name: my-project
windows:
  - window_name: editor
    panes:
      - shell_command:
          - vim
      - shell_command:
          - git status
```

```console
$ tmuxp load my-project.yaml
```

```{image} _static/tmuxp-demo.gif
:width: 888
:height: 589
:loading: lazy
```

```{toctree}
:hidden:

quickstart
cli/index
configuration/index
topics/index
internals/index
project/index
history
```

```{toctree}
:hidden:
:caption: More

about_tmux
migration
Comparison <comparison>
glossary
MCP <https://tmuxp-mcp.git-pull.com>
GitHub <https://github.com/tmux-python/tmuxp>
```
