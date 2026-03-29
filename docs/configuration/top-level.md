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

## Lifecycle hooks

Workspace configs support four lifecycle hooks that run shell commands at different stages of the session lifecycle:

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
| `on_project_start` | Before session build (new session creation only) |
| `on_project_restart` | When reattaching to an existing session (confirmed attach only) |
| `on_project_exit` | When the last client detaches (tmux `client-detached` hook) |
| `on_project_stop` | Before `tmuxp stop` kills the session |

Each hook accepts a string (single command) or a list of strings (multiple commands run sequentially).

```yaml
on_project_start:
  - notify-send "Starting"
  - ./setup.sh
```

```{note}
These hooks are inspired by tmuxinator's lifecycle hooks but have tmuxp-specific semantics.
`on_project_start` only fires on new session creation (not on reattach, append, or `--here`).
`on_project_restart` only fires when you confirm reattaching to an existing session.
```

```{note}
`on_project_exit` uses tmux's `client-detached` hook, but tmuxp guards it with `#{session_attached} == 0` so the command only runs when the **last** client detaches. This avoids repeated teardown in multi-client sessions. Unlike tmuxinator's wrapper-process hook, tmuxp keeps the hook on the session itself for the session lifetime.
```

## Pane titles

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
| `enable_pane_titles` | session | Enable pane border titles (`true`/`false`) |
| `pane_title_position` | session | Position of the title bar (`top`/`bottom`) |
| `pane_title_format` | session | Format string using tmux variables |
| `title` | pane | Title text for an individual pane |

```{note}
These correspond to tmuxinator's `enable_pane_titles`, `pane_title_position`, `pane_title_format`, and named pane (hash-key) syntax.
```

## Config templating

Workspace configs support `{{ variable }}` placeholders that are rendered before YAML/JSON parsing. Pass values via `--set KEY=VALUE` on the command line:

```yaml
session_name: "{{ project }}"
start_directory: "~/code/{{ project }}"
windows:
  - window_name: main
    panes:
      - echo "Working on {{ project }}"
```

```console
$ tmuxp load --set project=myapp mytemplate.yaml
```

```{note}
Values containing `{{ }}` must be quoted in YAML to prevent parse errors.
```

See {ref}`cli-load` for full CLI usage.

## synchronize

Window-level shorthand for setting `synchronize-panes`. Accepts `before`, `after`, or `true`:

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
| `before` | Enable synchronize-panes before sending pane commands |
| `after` | Enable synchronize-panes after sending pane commands |
| `true` | Same as `before` |

```{note}
This corresponds to tmuxinator's `synchronize` window key. The `before` and `true` values are accepted for compatibility but `after` is recommended.
```

## shell_command_after

Window-level key. Commands are sent to every pane in the window after all panes have been created and their individual commands executed:

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

## clear

Window-level boolean. When `true`, sends `clear` to every pane after all commands (including `shell_command_after`) have completed:

```yaml
session_name: myproject
windows:
  - window_name: dev
    clear: true
    panes:
      - cd src
      - cd tests
```
