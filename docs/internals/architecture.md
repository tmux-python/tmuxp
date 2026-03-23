# Architecture

How the tmuxp CLI dispatches commands to the underlying library.

## Request Flow

```
tmuxp CLI (argparse)
    │
    ├── tmuxp load ──→ workspace.loader ──→ workspace.builder ──→ libtmux
    ├── tmuxp freeze ──→ workspace.freezer ──→ libtmux
    ├── tmuxp convert ──→ _internal.config_reader
    ├── tmuxp shell ──→ libtmux (interactive)
    └── tmuxp ls/search ──→ workspace.finders
```

## Key Components

### CLI Layer (`tmuxp.cli`)

The CLI uses Python's `argparse` with a custom formatter ({mod}`tmuxp.cli._formatter`).
Each subcommand lives in its own module under `tmuxp.cli`.

The entry point is `tmuxp.cli.cli()`, registered as a console script in `pyproject.toml`.

### Workspace Layer (`tmuxp.workspace`)

The workspace layer handles configuration lifecycle:

1. **Finding**: {mod}`tmuxp.workspace.finders` locates config files
2. **Loading**: {mod}`tmuxp.workspace.loader` reads and validates configs
3. **Building**: {mod}`tmuxp.workspace.builder` creates tmux sessions via libtmux
4. **Freezing**: {mod}`tmuxp.workspace.freezer` exports running sessions

### Library Layer (libtmux)

tmuxp delegates all tmux operations to [libtmux](https://libtmux.git-pull.com/).
The `WorkspaceBuilder` creates libtmux `Server`, `Session`, `Window`, and `Pane`
objects to construct the requested workspace.
