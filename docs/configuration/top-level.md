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
