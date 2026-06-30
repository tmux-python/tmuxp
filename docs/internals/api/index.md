(api)=

# API Reference

This is the internal Python API — the modules tmuxp's CLI is built from,
documented for contributors and plugin authors. Everyday use goes through the
{ref}`CLI <cli>`; to drive tmux from Python directly, reach for
[libtmux](https://libtmux.git-pull.com/) instead.

:::{seealso}
See {ref}`libtmux's API <libtmux:api>` and {ref}`Quickstart <libtmux:quickstart>` to see how you can control
tmux via python API calls.
:::

::::{grid} 1 2 3 3
:gutter: 2 2 3 3

:::{grid-item-card} Workspace
:link: workspace/index
:link-type: doc
Finding, loading, building, and freezing sessions.
:::

:::{grid-item-card} CLI modules
:link: cli/index
:link-type: doc
The {mod}`argparse` commands behind each subcommand.
:::

:::{grid-item-card} Plugin API
:link: plugin
:link-type: doc
The {class}`~tmuxp.plugin.TmuxpPlugin` base class and its hooks.
:::

:::{grid-item-card} Internal helpers
:link: _internal/index
:link-type: doc
Config reader, colors, and private path helpers.
:::

:::{grid-item-card} Exceptions
:link: exc
:link-type: doc
The {exc}`~tmuxp.exc.TmuxpException` hierarchy.
:::

:::{grid-item-card} Logging
:link: log
:link-type: doc
Loggers and user-facing echo helpers.
:::

:::{grid-item-card} Shell
:link: shell
:link-type: doc
Internals of the interactive shell launcher.
:::

:::{grid-item-card} Utilities
:link: util
:link-type: doc
Assorted helpers used across tmuxp.
:::

:::{grid-item-card} Types
:link: types
:link-type: doc
Shared type definitions.
:::

::::

```{toctree}
:hidden:

_internal/index
cli/index
workspace/index
exc
log
plugin
shell
util
types
```
