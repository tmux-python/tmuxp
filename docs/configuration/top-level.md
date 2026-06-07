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

## Lifecycle Hooks

Workspace configs support four lifecycle hooks:

```yaml
session_name: myproject
on_project_start: notify-send "Starting myproject"
on_project_restart: notify-send "Reattaching to myproject"
on_project_exit: notify-send "Detached from myproject"
on_project_stop: notify-send "Stopping myproject"
windows:
  - window_name: main
    panes:
      -
```

| Hook | When it runs |
|------|-------------|
| `on_project_start` | Before a new session is built. |
| `on_project_restart` | Before reattaching to an existing session. |
| `on_project_exit` | When the last client detaches. |
| `on_project_stop` | Before `tmuxp stop` kills the session. |

Each hook accepts a string command or a list of command strings:

```yaml
on_project_start:
  - notify-send "Starting"
  - ./setup.sh
```

`on_project_start`, `on_project_restart`, and `on_project_stop` run through the
shell and block tmuxp until they finish. `on_project_exit` is different: it runs
via tmux's `client-detached` hook after tmuxp has already returned, so it never
blocks the command. Hook failures are logged and do not stop the tmuxp command.

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
