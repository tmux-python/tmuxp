(top-level)=
(top-level-config)=

# Top-level configuration

Top-level keys describe the session as a whole — its name, where it starts,
the tmux options it sets — and sit above the `windows` and `panes` that fill
it. Only `session_name` is required; leave the rest out and a workspace with
just a name and a list of windows loads fine. This page covers `session_name`
and the keys for choosing a workspace builder. For the full set of session,
window, and pane keys, work through {ref}`examples`.

## `session_name`

The name tmux gives the session — and the name tmuxp checks against when it
decides whether that session is already running. It need not match the
workspace filename.

For example, _apple.yaml_:

```yaml
session_name: banana
windows:
  - panes:
      -
```

Load it detached:

```console
$ tmuxp load ./apple.yaml -d
```

tmuxp reads _apple.yaml_ from the current directory and builds a tmux session
called _banana_ in the background — `-d` is detached. Attach to it with tmux
directly:

```console
$ tmux attach -t banana
```

## Workspace builder keys

A workspace file can also choose a custom builder and tune its behavior with
`workspace_builder`, `workspace_builder_paths`, and `workspace_builder_options`.
Most workspaces never set these — leave them out and you get tmuxp's built-in
classic builder.

```{seealso}
{ref}`workspace-builders`
```
