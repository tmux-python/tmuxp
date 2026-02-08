# Tmuxinator Parity Analysis

*Last updated: 2026-02-08*
*Tmuxinator version analyzed: 3.3.7*
*tmuxp version: 1.47.0+*

## Features tmuxinator has that tmuxp lacks

### 1. Project Hooks (Lifecycle Events)

**Source**: `lib/tmuxinator/hooks/project.rb`, `assets/template.erb`

tmuxinator has 5 lifecycle hooks:

| Hook | Description | tmuxp equivalent |
|---|---|---|
| `on_project_start` | Runs on every `start` invocation | No equivalent |
| `on_project_first_start` | Runs only when session doesn't exist yet | `before_script` (partial — runs before windows, but kills session on failure) |
| `on_project_restart` | Runs when attaching to existing session | Plugin `reattach()` (requires writing a plugin) |
| `on_project_exit` | Runs when detaching from session | No equivalent |
| `on_project_stop` | Runs on `tmuxinator stop` | No equivalent (tmuxp has no `stop` command) |

**Gap**: tmuxp's `before_script` is a partial equivalent of `on_project_first_start` — it runs before windows are created and kills the session on failure. tmuxp has no equivalent for `on_project_start` (runs every time, including reattach), no hooks for detach/exit/stop events, and no distinction between first start vs. restart.

**WorkspaceBuilder requirement**: Add config keys for `on_project_start`, `on_project_first_start`, `on_project_restart`, `on_project_exit`, `on_project_stop`. The exit/stop hooks require shell integration (trap signals, set-hook in tmux).

### 2. Stop/Kill Session Command

**Source**: `lib/tmuxinator/cli.rb` (`stop`, `stop_all`), `assets/template-stop.erb`

tmuxinator provides:

```bash
tmuxinator stop <project>    # Kill specific session + run on_project_stop hook
tmuxinator stop-all           # Kill all tmuxinator-managed sessions
```

**Gap**: tmuxp has no `stop` or `kill` command. Users must use `tmux kill-session` directly, which skips any cleanup hooks.

### 3. Session Name Override at Load Time

**Source**: `lib/tmuxinator/cli.rb` (`--name` / `-n` option)

```bash
tmuxinator start myproject --name custom-session-name
```

**Gap**: tmuxp has `tmuxp load -s <name>` which provides this. **No gap** — tmuxp already supports this.

### 4. Startup Window / Startup Pane Selection

**Source**: `lib/tmuxinator/project.rb` (`startup_window`, `startup_pane`)

```yaml
startup_window: editor      # Select this window after build
startup_pane: 1              # Select this pane within the startup window
```

**Gap**: tmuxp supports `focus: true` on windows and panes (boolean), which is equivalent but syntactically different. The `startup_window` key allows referencing by name or index (rendered as `"#{name}:#{value}"`). **Partial parity** — tmuxp can achieve this but uses a different mechanism (`focus` key on individual windows/panes rather than a centralized key).

### 5. Pane Synchronization

**Source**: `lib/tmuxinator/window.rb` (`synchronize`)

```yaml
windows:
  - editor:
      synchronize: true      # or "before" or "after"
      panes:
        - vim
        - vim
```

- `synchronize: true` / `synchronize: before` — enable pane sync before running pane commands
- `synchronize: after` — enable pane sync after running pane commands

**Gap**: tmuxp has no `synchronize` config key. Users would need to set `synchronize-panes on` via `options` manually, but this doesn't support the before/after distinction.

**WorkspaceBuilder requirement**: Add `synchronize` key to window config with `before`/`after`/`true`/`false` values.

### 6. Pane Titles

**Source**: `lib/tmuxinator/project.rb`, `lib/tmuxinator/pane.rb`

```yaml
enable_pane_titles: true
pane_title_position: top
pane_title_format: "#{pane_index}: #{pane_title}"
windows:
  - editor:
      panes:
        - my-editor: vim    # "my-editor" becomes the pane title
```

**Gap**: tmuxp has no pane title support. Named panes in tmuxinator (hash syntax: `pane_name: command`) set both a title and commands.

**WorkspaceBuilder requirement**: Add session-level `enable_pane_titles`, `pane_title_position`, `pane_title_format` keys. Add per-pane `title` key. Issue `select-pane -T <title>` after pane creation.

### 7. ERB Templating / Variable Interpolation

**Source**: `lib/tmuxinator/project.rb` (`parse_settings`, `render_template`)

```bash
tmuxinator start myproject env=production port=3000
```

```yaml
# config.yml
root: ~/apps/<%= @settings["app"] %>
windows:
  - server:
      panes:
        - rails server -p <%= @settings["port"] || 3000 %>
```

**Gap**: tmuxp has no config templating. Environment variable expansion (`$VAR`) is supported in `start_directory` paths, but not arbitrary variable interpolation in config values.

**WorkspaceBuilder requirement**: This is an architectural difference. tmuxp could support Jinja2 templating or Python string formatting, but this is a significant feature addition.

### 8. Wemux Support

**Source**: `lib/tmuxinator/wemux_support.rb`, `assets/wemux_template.erb`

```yaml
tmux_command: wemux
```

**Gap**: tmuxp has no wemux support. libtmux is tightly bound to the `tmux` command.

**WorkspaceBuilder requirement**: Allow configurable tmux command binary. Requires libtmux changes.

### 9. Debug / Dry-Run Output

**Source**: `lib/tmuxinator/cli.rb` (`debug`)

```bash
tmuxinator debug myproject
```

Outputs the generated shell script without executing it.

**Gap**: tmuxp has no dry-run mode. Since tmuxp uses API calls rather than script generation, a dry-run would need to log the libtmux calls that *would* be made.

### 10. Config Management Commands

**Source**: `lib/tmuxinator/cli.rb`

| Command | Description |
|---|---|
| `tmuxinator new <name>` | Create new config from template |
| `tmuxinator copy <src> <dst>` | Copy existing config |
| `tmuxinator delete <name>` | Delete config (with confirmation) |
| `tmuxinator implode` | Delete ALL configs |
| `tmuxinator stop <project>` | Stop session + run hooks |
| `tmuxinator stop-all` | Stop all managed sessions |

**Gap**: tmuxp has `edit` but not `new`, `copy`, `delete`, `implode`, or `stop` commands.

### 11. `--no-pre-window` Flag

**Source**: `lib/tmuxinator/cli.rb`

```bash
tmuxinator start myproject --no-pre-window
```

Skips `pre_window` commands. Useful for debugging.

**Gap**: tmuxp has no equivalent flag to skip `shell_command_before`.

### 12. `--here` Equivalent

**Source**: teamocil provides `--here` to reuse the current window. tmuxinator has no `--here` per se but tmuxp also lacks this.

**Gap**: Neither tmuxp nor tmuxinator has this; teamocil does.

### 13. Create Config from Running Session

**Source**: `lib/tmuxinator/cli.rb` (`new <name> <session>`)

```bash
tmuxinator new myproject existing-session-name
```

Creates a config file pre-populated from a running tmux session.

**Gap**: tmuxp has `tmuxp freeze` which exports to YAML/JSON. **Different approach, same result** — tmuxp's freeze is arguably more complete.

## Import Behavior Analysis

### Current Importer: `importers.py:import_tmuxinator`

**What it handles:**

| tmuxinator key | Mapped to | Status |
|---|---|---|
| `project_name` / `name` | `session_name` | ✓ Correct |
| `project_root` / `root` | `start_directory` | ✓ Correct |
| `cli_args` / `tmux_options` | `config` (extracts `-f`) | ⚠ Only handles `-f` flag, ignores `-L`, `-S` |
| `socket_name` | `socket_name` | ✓ Correct |
| `tabs` → `windows` | `windows` | ✓ Correct |
| `pre` + `pre_window` | `shell_command` + `shell_command_before` | ⚠ `shell_command` is not a valid tmuxp key |
| `pre` (alone) | `shell_command_before` | ✓ Correct |
| `rbenv` | appended to `shell_command_before` | ✓ Correct |
| Window hash key | `window_name` | ✓ Correct |
| Window `pre` | `shell_command_before` | ✓ Correct |
| Window `panes` | `panes` | ✓ Correct |
| Window `root` | `start_directory` | ✓ Correct |
| Window `layout` | `layout` | ✓ Correct |

**What it misses or handles incorrectly:**

| tmuxinator key | Issue |
|---|---|
| `attach` | Not imported. tmuxp uses CLI flags instead. |
| `startup_window` | Not imported. tmuxp uses `focus: true` on windows. |
| `startup_pane` | Not imported. tmuxp uses `focus: true` on panes. |
| `tmux_command` | Not imported. tmuxp has no equivalent. |
| `socket_path` | Not imported. tmuxp takes this via CLI. |
| `pre_tab` | Not imported (deprecated predecessor to `pre_window`). |
| `rvm` | Not imported (only `rbenv` is handled). |
| `post` | Not imported. tmuxp has no equivalent. |
| `synchronize` | Not imported. tmuxp has no equivalent. |
| `enable_pane_titles` | Not imported. tmuxp has no equivalent. |
| `pane_title_position` | Not imported. tmuxp has no equivalent. |
| `pane_title_format` | Not imported. tmuxp has no equivalent. |
| `on_project_start` | Not imported. tmuxp has no equivalent. |
| `on_project_first_start` | Not imported. Could map to `before_script`. |
| `on_project_restart` | Not imported. tmuxp has no equivalent. |
| `on_project_exit` | Not imported. tmuxp has no equivalent. |
| `on_project_stop` | Not imported. tmuxp has no equivalent. |
| Named panes (hash syntax) | Not imported. Pane names/titles are lost. |
| ERB templating | Not handled. YAML parsing will fail on ERB syntax. |
| `pre` + `pre_window` combo | Bug: sets `shell_command` which is not a tmuxp session-level key |

### Code Quality Issues in Importer

1. **Line 60**: When both `pre` and `pre_window` exist, the importer sets `tmuxp_workspace["shell_command"]` — but `shell_command` is not a valid session-level tmuxp key. The `pre` commands would be silently ignored.

2. **Line 36-49**: The `cli_args`/`tmux_options` handler only extracts `-f` (config file). It ignores `-L` (socket name) and `-S` (socket path) which could also appear in these fields.

3. **Line 79-101**: The window iteration uses `for k, v in window_dict.items()` which assumes windows are always dicts with a single key (the window name). This is correct for tmuxinator's format but fragile — if a window dict has multiple keys, only the last one is processed.

4. **Missing `pre_tab`**: The `pre_tab` deprecated predecessor to `pre_window` is not handled.

5. **Missing `rvm`**: Only `rbenv` is imported; `rvm` (another deprecated but still functional key) is ignored.

6. **No validation or warnings**: The importer silently drops unsupported keys with no feedback to the user.

## WorkspaceBuilder Requirements for 100% Feature Support

### Must-Have for Parity

1. **Pane synchronization** (`synchronize` window key) — `set-window-option synchronize-panes on/off`
2. **Pane titles** — `select-pane -T <title>`, `set-option pane-border-status top`, `set-option pane-border-format <fmt>`
3. **Startup window/pane selection** — Already achievable via `focus: true`, but could add `startup_window`/`startup_pane` as aliases
4. **Stop command** — `tmuxp stop <session>` to kill session

### Nice-to-Have

5. **Lifecycle hooks** — `on_project_start`, `on_project_first_start`, `on_project_restart`, `on_project_exit`, `on_project_stop`
6. **Config templating** — Jinja2 or Python format string support for config values
7. **Debug/dry-run** — Log tmux commands without executing
8. **Config management** — `tmuxp new`, `tmuxp copy`, `tmuxp delete` commands
9. **`--no-shell-command-before`** flag — Skip `shell_command_before` for debugging
10. **Custom tmux binary** — `tmux_command` key for wemux/byobu support (requires libtmux changes)
