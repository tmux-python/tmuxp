# Workflows

tmuxp is small enough to drop into a script, a CI job, or your daily startup
routine. This page collects a few patterns — running headless, branching on exit
codes, and turning a session you arranged by hand into a reusable file. None of
it is special machinery; it's the same `tmuxp load`, `freeze`, and exit codes you
already have.

## CI integration

You can build a tmux session inside a CI pipeline for integration testing. Load
it detached so nothing waits on a terminal:

```console
$ tmuxp load -d my-workspace.yaml
```

The `-d` flag loads the session in the background, which is what you want in a
headless environment.

## Scripting

tmuxp returns meaningful exit codes, so a script can tell success from failure
and branch on it. See {ref}`cli-exit-codes` for the full list.

## Automating development environments

You don't have to write a workspace file from scratch. Arrange a session the way
you like it, freeze it to capture the layout, then edit and replay it anywhere:

:::{mermaid}
:caption: Capture a session once, replay it anywhere.

flowchart LR
    arrange["arrange tmux by hand"] --> freeze["tmuxp freeze"]
    freeze --> yaml["workspace.yaml"]
    yaml --> edit["edit + commit"]
    edit --> load["tmuxp load"]
    load --> arrange
:::

1. Arrange your ideal tmux layout by hand.
2. Freeze it: `tmuxp freeze my-session`.
3. Edit the generated YAML to add commands.
4. Load it on any machine: `tmuxp load my-workspace.yaml`.

## User-level configuration

You can store workspace files in any of these, then load them by name from
anywhere:

- `~/.tmuxp/` (legacy)
- `~/.config/tmuxp/` (XDG default)
- a project-local `.tmuxp.yaml` or `.tmuxp/` directory
