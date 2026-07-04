(cli)=

(commands)=

# CLI Reference

::::{grid} 1 1 2 2
:gutter: 2 2 3 3

:::{grid-item-card} tmuxp load
:link: load
:link-type: doc
Load tmux sessions from workspace configs.
:::

:::{grid-item-card} tmuxp shell
:link: shell
:link-type: doc
Interactive Python shell with tmux context.
:::

:::{grid-item-card} tmuxp freeze
:link: freeze
:link-type: doc
Export running sessions to config files.
:::

:::{grid-item-card} tmuxp convert
:link: convert
:link-type: doc
Convert between YAML and JSON formats.
:::

:::{grid-item-card} Exit Codes
:link: exit-codes
:link-type: doc
Exit codes for scripting and automation.
:::

:::{grid-item-card} Recipes
:link: recipes
:link-type: doc
Copy-pasteable command invocations.
:::

::::

```{toctree}
:caption: General commands
:maxdepth: 1

load
shell
ls
search
stop
```

```{toctree}
:caption: Configuration
:maxdepth: 1

edit
import
convert
freeze
new
copy
delete
```

```{toctree}
:caption: Diagnostic
:maxdepth: 1

debug-info
```

```{toctree}
:caption: Completion
:maxdepth: 1

completion
```

```{toctree}
:caption: Reference
:maxdepth: 1

exit-codes
recipes
```

(cli-main)=

(tmuxp-main)=

## Main command

The `tmuxp` command is the entry point for all tmuxp operations. Use subcommands to load sessions, manage configurations, and interact with tmux.

### Command

```{eval-rst}
.. argparse::
    :module: tmuxp.cli
    :func: create_parser
    :prog: tmuxp
    :nosubcommands:

    subparser_name : @replace
        See :ref:`cli-ls`
```
