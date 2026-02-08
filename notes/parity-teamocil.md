# Teamocil Parity Analysis

*Last updated: 2026-02-08*
*Teamocil version analyzed: 1.4.2*
*tmuxp version: 1.47.0+*

## Version History Context

Teamocil has had two distinct config formats:

- **v0.x** (pre-1.0): Wrapped in `session:` key, used `splits` for panes, `filters` for before/after commands, `cmd` for pane commands
- **v1.x** (1.0–1.4.2): Simplified format — top-level `windows`, `panes` with `commands` key, `focus` support, window `options`

The current tmuxp importer (`importers.py:import_teamocil`) **targets the v0.x format**. It handles the `session:` wrapper, `splits`, `filters`, and `cmd` keys — all of which are v0.x-only constructs. It does **not** handle the v1.x format natively, though v1.x configs may partially work since the `windows`/`panes` structure is similar.

Note: teamocil v1.x does not create new sessions — it **renames** the current session (`rename-session`) and adds windows to it. This is fundamentally different from tmuxp/tmuxinator which create fresh sessions.

## Features teamocil has that tmuxp lacks

### 1. Session Rename (Not Create)

**Source**: `lib/teamocil/tmux/session.rb:18-20`

teamocil does not create a new session. It **renames** the current session via `rename-session` and adds windows to it. If no `name` is provided, it auto-generates one: `"teamocil-session-#{rand(1_000_000)}"`.

**Gap**: tmuxp always creates a new session (unless appending with `--append`). There is no way to rename and populate the current session.

### 2. `--here` Option (Reuse Current Window)

**Source**: `lib/teamocil/tmux/window.rb`, `lib/teamocil/utils/option_parser.rb`

```bash
teamocil --here my-layout
```

When `--here` is specified:
- First window: **renames** current window (`rename-window`) instead of creating a new one
- First window: sends `cd "<root>"` + `Enter` via `send-keys` to change directory (since no `-c` flag is available on an existing window)
- First window: decrements the window count when calculating base indices for subsequent windows
- Subsequent windows: created normally with `new-window`

**Gap**: tmuxp always creates new windows. There is no way to populate the current window with a layout.

**WorkspaceBuilder requirement**: Add `--here` CLI flag. For first window, use `rename-window` + `send-keys cd` instead of `new_window()`. Must also adjust window index calculation. This would require special handling in `WorkspaceBuilder.first_window_pass()`.

### 3. `--show` Option (Show Raw Config)

**Source**: `lib/teamocil/layout.rb`

```bash
teamocil --show my-layout
```

Outputs the raw YAML content of the layout file.

**Gap**: tmuxp has no equivalent. Users can `cat` the file manually.

### 4. `--debug` Option (Show Commands Without Executing)

**Source**: `lib/teamocil/layout.rb`

```bash
teamocil --debug my-layout
```

Outputs the tmux commands that would be executed, one per line, without running them.

**Gap**: tmuxp has no dry-run mode. Since tmuxp uses libtmux API calls rather than generating command strings, implementing this would require a logging/recording mode in the builder.

Note: teamocil also has `--list` (lists available layouts in `~/.teamocil/`) and `--edit` (opens layout file in `$EDITOR`). Both are available in tmuxp (`tmuxp ls`, `tmuxp edit`).

### 5. Window-Level `focus` Key

**Source**: `lib/teamocil/tmux/window.rb`

```yaml
windows:
  - name: editor
    focus: true
    panes:
      - vim
```

**Gap**: tmuxp **does** support `focus: true` on windows. **No gap**.

Note: teamocil handles window focus at the session level in `session.rb:24-25` — after all windows are created, it finds the focused window and issues `select-window`. tmuxp handles this the same way.

### 6. Pane-Level `focus` Key

**Source**: `lib/teamocil/tmux/pane.rb`

```yaml
panes:
  - commands:
      - vim
    focus: true
```

**Gap**: tmuxp **does** support `focus: true` on panes. **No gap**.

### 7. Window-Level `options` Key

**Source**: `lib/teamocil/tmux/window.rb`

```yaml
windows:
  - name: editor
    options:
      main-pane-width: '100'
```

Maps to `set-window-option -t <window> <key> <value>`.

**Gap**: tmuxp **does** support `options` on windows. **No gap**.

### 8. Multiple Commands Joined by Semicolon

**Source**: `lib/teamocil/tmux/pane.rb`

Teamocil joins multiple pane commands with `; ` and sends them as a single `send-keys` invocation:

```ruby
# Pane with commands: ["cd /path", "vim"]
# → send-keys "cd /path; vim"
```

**Gap**: tmuxp sends each command separately via individual `pane.send_keys()` calls. This is actually more reliable (each command gets its own Enter press), so this is a **behavioral difference** rather than a gap.

## v0.x vs v1.x Format Differences

| Feature | v0.x | v1.x (current) |
|---|---|---|
| Top-level wrapper | `session:` key | None (top-level `windows`) |
| Session name | `session.name` | `name` |
| Session root | `session.root` | (none, per-window only) |
| Panes key | `splits` | `panes` |
| Pane commands | `cmd` (string or list) | `commands` (list) |
| Before commands | `filters.before` (list) | (none) |
| After commands | `filters.after` (list) | (none) |
| Pane width | `width` (number) | (none) |
| Window clear | `clear` (boolean) | (none) |
| Pane focus | (none) | `focus` (boolean) |
| Window focus | (none) | `focus` (boolean) |
| Window options | (none) | `options` (hash) |
| Pane string shorthand | (none) | `- command_string` |

## Import Behavior Analysis

### Current Importer: `importers.py:import_teamocil`

**What it handles (v0.x format):**

| teamocil key | Mapped to | Status |
|---|---|---|
| `session` (wrapper) | Unwrapped | ✓ Correct |
| `session.name` | `session_name` | ✓ Correct |
| `session.root` | `start_directory` | ✓ Correct |
| Window `name` | `window_name` | ✓ Correct |
| Window `root` | `start_directory` | ✓ Correct |
| Window `layout` | `layout` | ✓ Correct |
| Window `clear` | `clear` | ⚠ Preserved but tmuxp doesn't use `clear` |
| Window `filters.before` | `shell_command_before` | ✓ Correct |
| Window `filters.after` | `shell_command_after` | ⚠ tmuxp doesn't support `shell_command_after` |
| `splits` → `panes` | `panes` | ✓ Correct |
| Pane `cmd` | `shell_command` | ✓ Correct |
| Pane `width` | Dropped | ⚠ Silently dropped with TODO comment |

**What it misses:**

| Feature | Issue |
|---|---|
| v1.x `commands` key | Not handled — only `cmd` (v0.x) is mapped |
| v1.x pane string shorthand | Not handled — expects dict with `cmd` key |
| v1.x `focus` (window) | Not imported |
| v1.x `focus` (pane) | Not imported |
| v1.x `options` (window) | Not imported |
| Session-level `name` (without `session:` wrapper) | Handled (uses `.get("name")`) |
| `with_env_var` (importer TODO) | Not handled — does not exist in current teamocil source |
| `cmd_separator` (importer TODO) | Not handled — does not exist in current teamocil source |

### Code Quality Issues in Importer

1. **Lines 144-149**: The `filters.before` and `filters.after` handling has redundant `for _b in` loops that serve no purpose. The inner assignment just reassigns the same value each iteration:
   ```python
   for _b in w["filters"]["before"]:
       window_dict["shell_command_before"] = w["filters"]["before"]
   ```
   This iterates N times but sets the same value each time. It should be a direct assignment.

2. **Lines 140-141**: `clear` is preserved in the config but tmuxp has no handling for it. It will be silently ignored during workspace building.

3. **Lines 147-149**: `shell_command_after` is set from `filters.after` but is not a tmuxp-supported key. It will be silently ignored during workspace building.

4. **Lines 161-163**: `width` is silently dropped with a TODO comment. No warning to the user.

5. **v1.x incompatibility**: The importer assumes v0.x format. A v1.x config with `commands` instead of `cmd`, or string panes, will not import correctly:
   - String pane `"git status"` → error (tries to access `p["cmd"]` on a string)
   - `commands: [...]` → not mapped to `shell_command`

6. **No format detection**: The importer doesn't attempt to detect whether the input is v0.x or v1.x format.

## WorkspaceBuilder Requirements for Full Parity

### Already Supported (No Changes Needed)

- Window `focus` — ✓
- Pane `focus` — ✓
- Window `options` — ✓
- Window `layout` — ✓
- Window `root`/`start_directory` — ✓
- Pane commands — ✓

### Gaps Requiring New Features

1. **Session rename mode** — teamocil renames the current session rather than creating a new one. tmuxp always creates a fresh session.

2. **`--here` flag** — Reuse current window for first window of layout. Requires `WorkspaceBuilder` to rename instead of create, and send `cd` for root directory.

3. **`--debug` / dry-run mode** — Log commands without executing. Architectural challenge since tmuxp uses libtmux API, not command strings.

4. **`shell_command_after`** — Commands run after pane commands. The importer preserves this from teamocil's `filters.after` but tmuxp has no support for it in the builder.

### Import-Only Fixes (No Builder Changes)

5. **v1.x format support** — The importer should handle:
   - `commands` key (v1.x) in addition to `cmd` (v0.x)
   - String pane shorthand
   - `focus` on windows and panes
   - `options` on windows

6. **Redundant loop cleanup** — Fix the `filters` handling code.

7. **Drop unsupported keys with warnings** — Instead of silently preserving `clear` or dropping `width`, warn the user.
