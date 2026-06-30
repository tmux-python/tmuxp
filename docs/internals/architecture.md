# Architecture

This page traces how a tmuxp command travels from the CLI down to libtmux, the
library that does the actual tmux work. Each subcommand takes its own short path
through one or two workspace modules:

:::{mermaid}
:caption: How each tmuxp subcommand reaches libtmux.

flowchart LR
    cli["tmuxp CLI (argparse)"]
    cli -->|load| loader["workspace.loader"]:::cmd
    loader --> builder["workspace.builder"]:::cmd
    builder --> libtmux["libtmux"]:::cmd
    cli -->|freeze| freezer["workspace.freezer"]:::cmd
    freezer --> libtmux
    cli -->|convert| reader["_internal.config_reader"]:::cmd
    cli -->|shell| interactive["libtmux (interactive)"]
    cli -->|"ls / search"| finders["workspace.finders"]:::cmd
:::

## Key Components

### CLI Layer (`tmuxp.cli`)

The CLI uses Python's {mod}`argparse` with a custom formatter ({mod}`tmuxp.cli._formatter`).
Each subcommand lives in its own module under {mod}`tmuxp.cli`.

The entry point is {func}`tmuxp.cli.cli`, registered as a console script in `pyproject.toml`.

### Workspace Layer (`tmuxp.workspace`)

The workspace layer handles configuration lifecycle:

1. **Finding**: {mod}`tmuxp.workspace.finders` locates config files
2. **Loading**: {mod}`tmuxp.workspace.loader` reads and validates configs
3. **Building**: {mod}`tmuxp.workspace.builder` creates tmux sessions via libtmux
4. **Freezing**: {mod}`tmuxp.workspace.freezer` exports running sessions

### Library Layer (libtmux)

tmuxp delegates all tmux operations to [libtmux](https://libtmux.git-pull.com/).
The {class}`~tmuxp.workspace.builder.classic.ClassicWorkspaceBuilder` creates
libtmux {class}`~libtmux.Server`, {class}`~libtmux.Session`, {class}`~libtmux.Window`,
and {class}`~libtmux.Pane` objects to construct the requested workspace.
