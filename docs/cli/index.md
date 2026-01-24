(cli)=

(commands)=

# Commands

```{toctree}
:caption: General commands
:maxdepth: 1

load
shell
ls
search
```

```{toctree}
:caption: Configuration
:maxdepth: 1

edit
import
convert
freeze
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
