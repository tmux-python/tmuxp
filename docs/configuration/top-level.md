(top-level)=
(top-level-config)=

# Top-level configuration

## `session_name`

Used for:

- tmux session name
- checking for existing sessions

Notes:

- Session names may differ from workspace filename.

  e.g. _apple.yaml_:

  ```yaml
  session_name: banana
  windows:
    - panes:
        -
  ```

  Load detached:

  ```console
  $ tmuxp load ./apple.yaml -d
  ```

  Above:

  - tmuxp loads a file named _apple.yaml_ from the current directory.
  - tmuxp built a tmux session called _banana_.
  - `-d` means _detached_, loading in background.

  ```console
  $ tmux attach -t banana
  ```

  Above: Use `tmux` directly to attach _banana_.

## Workspace builder keys

A workspace file can also select a custom builder and tune builder behavior with
`workspace_builder`, `workspace_builder_paths`, and `workspace_builder_options`.

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

Window-level shorthand for the final `synchronize-panes` state. tmuxp keeps
pane synchronization disabled while it builds panes and sends configured
commands, then restores the requested synchronized state after the window is
ready.

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
| `after` | Synchronize panes after tmuxp finishes building the window. |
| `before` | Compatibility alias for the same final synchronized state. |
| `true` | Compatibility alias for the same final synchronized state. |
| `false` | Force the final window state to unsynchronized. |

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

tmuxp keeps `synchronize-panes` disabled while `shell_command_after` runs, then
restores the final synchronized state afterward. This prevents tmux from
duplicating post-build commands across panes.

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
