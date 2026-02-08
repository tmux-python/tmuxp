# Tmuxinator Import Behavior

*Last updated: 2026-02-08*
*Importer: `src/tmuxp/workspace/importers.py:import_tmuxinator`*

## Syntax Differences (Translatable)

These are config keys/patterns that differ syntactically but can be automatically converted during import.

### 1. Session Name

| tmuxinator | tmuxp |
|---|---|
| `name: myproject` | `session_name: myproject` |
| `project_name: myproject` | `session_name: myproject` |

**Importer status**: ✓ Handled (lines 24-29)

### 2. Root Directory

| tmuxinator | tmuxp |
|---|---|
| `root: ~/project` | `start_directory: ~/project` |
| `project_root: ~/project` | `start_directory: ~/project` |

**Importer status**: ✓ Handled (lines 31-34)

### 3. Windows List Key

| tmuxinator | tmuxp |
|---|---|
| `tabs:` | `windows:` |
| `windows:` | `windows:` |

**Importer status**: ✓ Handled (lines 56-57)

### 4. Window Name Syntax

| tmuxinator | tmuxp |
|---|---|
| `- editor:` (hash key) | `- window_name: editor` |

**Importer status**: ✓ Handled (lines 79-81)

### 5. Window Root

| tmuxinator | tmuxp |
|---|---|
| `root: ./src` (under window hash) | `start_directory: ./src` |

**Importer status**: ✓ Handled (lines 96-97)

### 6. Window Pre-Commands

| tmuxinator | tmuxp |
|---|---|
| `pre: "source .env"` (under window hash) | `shell_command_before: ["source .env"]` |

**Importer status**: ✓ Handled (lines 92-93)

### 7. Socket Name

| tmuxinator | tmuxp |
|---|---|
| `socket_name: myapp` | `socket_name: myapp` |

**Importer status**: ✓ Handled (lines 51-52). Note: tmuxp doesn't use `socket_name` as a config key in `WorkspaceBuilder` — it's a CLI flag. The importer preserves it but it may not be used.

### 8. CLI Args / Tmux Options → Config File

| tmuxinator | tmuxp |
|---|---|
| `cli_args: "-f ~/.tmux.special.conf"` | `config: ~/.tmux.special.conf` |
| `tmux_options: "-f ~/.tmux.special.conf"` | `config: ~/.tmux.special.conf` |

**Importer status**: ⚠ Partially handled (lines 36-49). Only extracts `-f` flag value. Other flags like `-L` (socket name) and `-S` (socket path) in `cli_args`/`tmux_options` are silently included in the `config` value, which is incorrect — `config` should only be a file path.

### 9. Rbenv

| tmuxinator | tmuxp |
|---|---|
| `rbenv: 2.7.0` | `shell_command_before: ["rbenv shell 2.7.0"]` |

**Importer status**: ✓ Handled (lines 72-77)

### 10. Pre / Pre-Window Commands

| tmuxinator | tmuxp |
|---|---|
| `pre: "cmd"` (session-level, alone) | `shell_command_before: ["cmd"]` |
| `pre_window: "cmd"` + `pre: "cmd"` | `shell_command: "cmd"` + `shell_command_before: ["cmd"]` |

**Importer status**: ⚠ Bug (lines 59-70). When both `pre` and `pre_window` exist, the importer sets `shell_command` (not a valid tmuxp session-level key) for `pre` and `shell_command_before` for `pre_window`. The `pre` commands are lost.

**Correct mapping**: Both should map to `shell_command_before`, with `pre` commands first, then `pre_window` commands.

### 11. Window as String/List

| tmuxinator | tmuxp |
|---|---|
| `- editor: vim` | `- window_name: editor` + `panes: [vim]` |
| `- editor: [vim, "git status"]` | `- window_name: editor` + `panes: [vim, "git status"]` |

**Importer status**: ✓ Handled (lines 83-90)

### 12. `startup_window` → `focus`

| tmuxinator | tmuxp |
|---|---|
| `startup_window: editor` | Set `focus: true` on the matching window |

**Importer status**: ✗ Not handled. Could be translated by finding the matching window and adding `focus: true`.

### 13. `startup_pane` → `focus`

| tmuxinator | tmuxp |
|---|---|
| `startup_pane: 1` | Set `focus: true` on the matching pane |

**Importer status**: ✗ Not handled. Could be translated by finding the pane at the given index and adding `focus: true`.

### 14. `pre_tab` → `shell_command_before`

| tmuxinator | tmuxp |
|---|---|
| `pre_tab: "source .env"` | `shell_command_before: ["source .env"]` |

**Importer status**: ✗ Not handled. `pre_tab` is a deprecated predecessor to `pre_window` (not an alias — it was renamed).

### 15. `rvm` → `shell_command_before`

| tmuxinator | tmuxp |
|---|---|
| `rvm: ruby-2.7@mygemset` | `shell_command_before: ["rvm use ruby-2.7@mygemset"]` |

**Importer status**: ✗ Not handled. Only `rbenv` is mapped; `rvm` is ignored.

### 16. `socket_path`

| tmuxinator | tmuxp |
|---|---|
| `socket_path: /tmp/my.sock` | (CLI `-S /tmp/my.sock`) |

**Importer status**: ✗ Not handled. `socket_path` is a tmuxinator config key (takes precedence over `socket_name`) but the importer ignores it. tmuxp takes socket path via CLI `-S` flag only.

### 17. `attach: false` → CLI Flag

| tmuxinator | tmuxp |
|---|---|
| `attach: false` | `tmuxp load -d` (detached mode) |

**Importer status**: ✗ Not handled. Could add a comment or warning suggesting `-d` flag.

## Limitations (tmuxp Needs to Add Support)

These are features that cannot be imported because tmuxp lacks the underlying capability.

### 1. Lifecycle Hooks

**What it does in tmuxinator**: Five project hooks (`on_project_start`, `on_project_first_start`, `on_project_restart`, `on_project_exit`, `on_project_stop`) allow running arbitrary commands at different lifecycle stages.

**Why it can't be imported**: tmuxp only has `before_script` (partial equivalent to `on_project_first_start`). The exit/stop/restart hooks require tmux `set-hook` integration or signal trapping that tmuxp doesn't support.

**What tmuxp would need to add**: Session-level `on_project_start`, `on_project_first_start`, `on_project_restart`, `on_project_exit`, `on_project_stop` config keys, plus builder logic to execute them at appropriate points. For exit/stop hooks, tmuxp would need a `stop` command and tmux `set-hook` for `client-detached`.

### 2. Pane Synchronization

**What it does in tmuxinator**: `synchronize: true/before/after` on windows enables `synchronize-panes` option, with control over whether sync happens before or after pane commands.

**Why it can't be imported**: tmuxp has no `synchronize` config key. While users can set `synchronize-panes` via `options`, the before/after timing distinction requires builder support.

**What tmuxp would need to add**: `synchronize` key on windows with `before`/`after`/`true`/`false` values. Builder should call `set-window-option synchronize-panes on` at the appropriate point.

### 3. Pane Titles

**What it does in tmuxinator**: Named pane syntax (`pane_name: command`) sets pane titles via `select-pane -T`. Session-level `enable_pane_titles`, `pane_title_position`, `pane_title_format` control display.

**Why it can't be imported**: tmuxp has no pane title support.

**What tmuxp would need to add**: Per-pane `title` key, session-level title configuration. Builder calls `select-pane -T <title>` after pane creation.

### 4. ERB Templating

**What it does in tmuxinator**: Config files are processed through ERB before YAML parsing. Supports `<%= @settings["key"] %>` interpolation and full Ruby expressions. Variables passed via `key=value` CLI args.

**Why it can't be imported**: ERB is a Ruby templating system. The importer receives already-parsed YAML (ERB would have already been processed in Ruby). When importing a raw tmuxinator config file with ERB syntax, YAML parsing will fail.

**What tmuxp would need to add**: Either a Jinja2 templating pass, Python string formatting, or environment variable expansion in config values. This is a significant architectural feature.

### 5. Wemux Support

**What it does in tmuxinator**: `tmux_command: wemux` uses an alternate template and wemux-specific commands.

**Why it can't be imported**: tmuxp and libtmux are tightly bound to the `tmux` binary.

**What tmuxp would need to add**: Configurable tmux binary path in libtmux's `Server` class.

### 6. `--no-pre-window` Flag

**What it does in tmuxinator**: Skips all `pre_window` commands when starting a session. Useful for debugging.

**Why it can't be imported**: This is a runtime behavior, not a config key.

**What tmuxp would need to add**: `--no-shell-command-before` CLI flag on `tmuxp load`.

## Summary Table

| tmuxinator Feature | Import Status | Classification |
|---|---|---|
| `name`/`project_name` → `session_name` | ✓ Handled | Difference |
| `root`/`project_root` → `start_directory` | ✓ Handled | Difference |
| `tabs` → `windows` | ✓ Handled | Difference |
| `socket_name` | ✓ Handled | Difference |
| `cli_args`/`tmux_options` → `config` | ⚠ Partial | Difference (needs fix) |
| `rbenv` → `shell_command_before` | ✓ Handled | Difference |
| `pre` → `shell_command_before` | ⚠ Bug when combined with `pre_window` | Difference (needs fix) |
| Window hash syntax | ✓ Handled | Difference |
| Window `root`/`pre`/`layout`/`panes` | ✓ Handled | Difference |
| `rvm` → `shell_command_before` | ✗ Missing | Difference (needs add) |
| `pre_tab` → `shell_command_before` | ✗ Missing | Difference (needs add) |
| `startup_window` → `focus` | ✗ Missing | Difference (needs add) |
| `startup_pane` → `focus` | ✗ Missing | Difference (needs add) |
| `socket_path` | ✗ Missing | Difference (needs add) |
| `attach: false` | ✗ Missing | Difference (needs add) |
| `on_project_*` hooks | ✗ Missing | **Limitation** |
| `synchronize` | ✗ Missing | **Limitation** |
| `enable_pane_titles` / titles | ✗ Missing | **Limitation** |
| ERB templating | ✗ Missing | **Limitation** |
| `tmux_command` (wemux) | ✗ Missing | **Limitation** |
| `--no-pre-window` | N/A (runtime flag) | **Limitation** |
