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

## Pane Titles

Enable pane border titles to display labels on each pane:

```yaml
session_name: myproject
enable_pane_titles: true
pane_title_position: top
pane_title_format: "#{pane_index}: #{pane_title}"
windows:
  - window_name: dev
    panes:
      - title: editor
        shell_command:
          - vim
      - title: tests
        shell_command:
          - uv run pytest --watch
      - shell_command:
          - git status
```

| Key | Level | Description |
|-----|-------|-------------|
| `enable_pane_titles` | session | Enable pane border titles (`true` or `false`). |
| `pane_title_position` | session | Position of the title bar (`top`, `bottom`, or `off`). |
| `pane_title_format` | session | Format string using tmux variables. |
| `title` | pane | Title text for an individual pane. |

```{note}
tmux ignores empty pane titles — `title: ""` logs a warning and keeps the
default label. Use a single space (`title: " "`) to visually blank one.
```

## synchronize

Window-level shorthand for setting `synchronize-panes`. It accepts
`before`, `after`, or `true`:

```yaml
session_name: sync-demo
windows:
  - window_name: synced
    synchronize: after
    panes:
      - echo pane0
      - echo pane1
  - window_name: not-synced
    panes:
      - echo pane0
      - echo pane1
```

| Value | Behavior |
|-------|----------|
| `before` | Enable `synchronize-panes` before sending pane commands. |
| `after` | Enable `synchronize-panes` after sending pane commands. |
| `true` | Same as `before`. |

## shell_command_after

Window-level commands sent to every pane after all panes have been created and
their individual commands executed:

```yaml
session_name: myproject
windows:
  - window_name: servers
    shell_command_after:
      - echo "All panes ready"
    panes:
      - ./start-api.sh
      - ./start-worker.sh
```

`shell_command_after` runs before `options_after`, so `synchronize: after` does
not duplicate the commands across synchronized panes.

Entries accept the same command mappings as `shell_command` — `enter`,
`sleep_before`, and `sleep_after` apply per command (sleeps run once per
command, before and after it is sent to every pane):

```yaml
shell_command_after:
  - cmd: ./healthcheck.sh
    sleep_before: 2
  - cmd: tail -f app.log
    enter: false
```

## clear

Window-level boolean. When `true`, sends `clear` to every pane after all
commands, including `shell_command_after`, have completed:

```yaml
session_name: myproject
windows:
  - window_name: dev
    clear: true
    panes:
      - cd src
      - cd tests
```
