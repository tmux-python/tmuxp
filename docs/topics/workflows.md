# Workflows

## CI Integration

tmuxp can set up tmux sessions in CI pipelines for integration testing:

```console
$ tmuxp load -d my-workspace.yaml
```

The `-d` flag loads the session in detached mode, useful for headless environments.

## Scripting

tmuxp's exit codes enable scripting and error handling. See
[Exit Codes](../cli/exit-codes.md) for the complete list.

## Automating Development Environments

Use tmuxp to codify your development environment:

1. Set up your ideal tmux layout manually
2. Freeze it: `tmuxp freeze my-session`
3. Edit the generated YAML to add commands
4. Load it on any machine: `tmuxp load my-workspace.yaml`

## User-Level Configuration

Workspace configs can be stored in:
- `~/.tmuxp/` (legacy)
- `~/.config/tmuxp/` (XDG default)
- Project-local `.tmuxp.yaml` or `.tmuxp/` directory
