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
Hooks block tmuxp until they complete — there is no time limit. Hook output is
captured rather than shown (failures log the output at debug level), so a
long-running hook looks quiet; `Ctrl-C` interrupts both the hook and tmuxp.
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
