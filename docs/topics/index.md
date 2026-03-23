(topics)=

# Topics

Conceptual guides and workflow documentation.

::::{grid} 2
:gutter: 3

:::{grid-item-card} Workflows
:link: workflows
:link-type: doc
CI integration, scripting, and automation patterns.
:::

:::{grid-item-card} Plugins
:link: plugins
:link-type: doc
Plugin system for custom behavior.
:::

:::{grid-item-card} Library vs CLI
:link: library-vs-cli
:link-type: doc
When to use tmuxp CLI vs libtmux directly.
:::

:::{grid-item-card} Troubleshooting
:link: troubleshooting
:link-type: doc
Common shell, PATH, and tmux issues.
:::

::::

## Compared to tmuxinator / teamocil

tmuxp, [tmuxinator](https://github.com/aziz/tmuxinator), and
[teamocil](https://github.com/remiprev/teamocil) all load tmux sessions
from config files. Key differences: tmuxp is Python (not Ruby), builds
sessions through [libtmux](https://libtmux.git-pull.com/)'s ORM layer
instead of raw shell commands, supports JSON and YAML, and can
[freeze](../cli/freeze.md) running sessions back to config.

```{toctree}
:hidden:

workflows
plugins
library-vs-cli
troubleshooting
```
