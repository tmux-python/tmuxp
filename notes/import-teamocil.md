# Teamocil Import Behavior

*Last updated: 2026-03-06*
*Importer: `src/tmuxp/workspace/importers.py:import_teamocil`*

## Format Detection Problem

Teamocil has two distinct config formats:

- **v0.x** (pre-1.0): `session:` wrapper, `splits`, `filters`, `cmd`
- **v1.x** (1.0–1.4.2): Flat `windows`, `panes`, `commands`, `focus`, `options`

The current importer **targets v0.x only**. It handles v0.x-specific constructs (`session:` wrapper, `splits`, `filters.before`, `filters.after`, `cmd`) but does not handle v1.x-specific constructs (`commands`, string pane shorthand, `focus`, window `options`).

Since teamocil 1.4.2 uses the v1.x format, the importer is outdated for current teamocil configs.

## Syntax Differences (Translatable)

### 1. Session Wrapper (v0.x)

| teamocil v0.x | tmuxp |
|---|---|
| `session:` + `name:` + `windows:` | `session_name:` + `windows:` |

**Importer status**: ✓ Handled (lines 127-128). Unwraps the `session:` key.

### 2. Session Name

| teamocil | tmuxp |
|---|---|
| `name: my-layout` | `session_name: my-layout` |

**Importer status**: ✓ Handled (line 130)

### 3. Session Root (v0.x)

| teamocil v0.x | tmuxp |
|---|---|
| `session.root: ~/project` | `start_directory: ~/project` |

**Importer status**: ✓ Handled (lines 132-133). Note: v1.x teamocil has no session-level root.

### 4. Window Name

| teamocil | tmuxp |
|---|---|
| `name: editor` | `window_name: editor` |

**Importer status**: ✓ Handled (line 138)

### 5. Window Root

| teamocil | tmuxp |
|---|---|
| `root: ~/project` | `start_directory: ~/project` |

**Importer status**: ✓ Handled (lines 151-152)

### 6. Window Layout

| teamocil | tmuxp |
|---|---|
| `layout: main-vertical` | `layout: main-vertical` |

**Importer status**: ✓ Handled (lines 166-167). Same key name, direct pass-through.

### 7. Splits → Panes (v0.x)

| teamocil v0.x | tmuxp |
|---|---|
| `splits:` | `panes:` |

**Importer status**: ✓ Handled (lines 154-155). Renames key.

### 8. Pane `cmd` → `shell_command` (v0.x)

| teamocil v0.x | tmuxp |
|---|---|
| `cmd: vim` | `shell_command: vim` |
| `cmd: [cd /path, vim]` | `shell_command: [cd /path, vim]` |

**Importer status**: ✓ Handled (lines 159-160). Renames key.

### 9. Filters Before → Shell Command Before (v0.x)

| teamocil v0.x | tmuxp |
|---|---|
| `filters: { before: [cmd1, cmd2] }` | `shell_command_before: [cmd1, cmd2]` |

**Importer status**: ⚠ Handled but with redundant loop (lines 144-146). The `for _b in` loop iterates uselessly — the assignment inside is the same each iteration. Should be a direct assignment.

### 10. Pane `commands` → `shell_command` (v1.x)

| teamocil v1.x | tmuxp |
|---|---|
| `commands: [git pull, vim]` | `shell_command: [git pull, vim]` |

**Importer status**: ✗ Not handled. The v1.x `commands` key is not mapped. Only `cmd` (v0.x) is recognized.

### 11. String Pane Shorthand (v1.x)

| teamocil v1.x | tmuxp |
|---|---|
| `- git status` (string in panes list) | `- shell_command: [git status]` |

**Importer status**: ✗ Not handled. The importer expects each pane to be a dict (tries `p["cmd"]`). String panes will cause a `TypeError`.

### 12. Window Focus (v1.x)

| teamocil v1.x | tmuxp |
|---|---|
| `focus: true` (on window) | `focus: true` |

**Importer status**: ✗ Not handled. The key is not imported.

### 13. Pane Focus (v1.x)

| teamocil v1.x | tmuxp |
|---|---|
| `focus: true` (on pane) | `focus: true` |

**Importer status**: ✗ Not handled. The key is not imported.

### 14. Window Options (v1.x)

| teamocil v1.x | tmuxp |
|---|---|
| `options: { main-pane-width: '100' }` | `options: { main-pane-width: '100' }` |

**Importer status**: ✗ Not handled. Same key name in tmuxp, but not imported from teamocil configs.

## Limitations (tmuxp Needs to Add Support)

### 1. `--here` Flag (Reuse Current Window)

**What it does in teamocil**: First window is renamed and reused instead of creating a new one. Root directory applied via `cd` command.

**Why it can't be imported**: This is a runtime CLI flag, not a config key.

**What tmuxp would need to add**: `--here` flag on `tmuxp load` that tells WorkspaceBuilder to rename the current window for the first window instead of creating new.

### 2. Filters After / `shell_command_after` (v0.x)

**What it does in teamocil**: `filters.after` commands run after pane commands.

**Why it can't be imported**: The importer maps this to `shell_command_after`, but tmuxp has no support for this key in the WorkspaceBuilder. The key is silently ignored.

**What tmuxp would need to add**: `shell_command_after` key on windows/panes. Builder would send these commands after all pane `shell_command` entries.

### 3. Pane Width (v0.x)

**What it does in teamocil v0.x**: `width` on splits to set pane width.

**Why it can't be imported**: tmuxp drops this with a TODO comment. tmuxp relies on tmux layouts for pane geometry.

**What tmuxp would need to add**: Per-pane `width`/`height` keys. Builder would use `resize-pane -x <width>` or `resize-pane -y <height>` after split. Alternatively, support custom layout strings.

### 4. Window Clear (v0.x)

**What it does in teamocil v0.x**: `clear: true` on windows.

**Why it can't be imported**: The importer preserves the `clear` key but tmuxp doesn't act on it.

**What tmuxp would need to add**: `clear` key on windows. Builder would send `clear` (or `send-keys C-l`) after pane creation.

## Import-Only Fixes (No Builder Changes)

### 5. `with_env_var` (v0.x only)

**Verified**: `with_env_var` exists in teamocil's v0.x (`0.4-stable` branch) at `lib/teamocil/layout/window.rb`. When `true` (the default), it exports `TEAMOCIL=1` environment variable in each pane's command chain. Removed in v1.x rewrite.

tmuxp's `environment` key would be the natural mapping: `environment: { TEAMOCIL: "1" }`. However, since this was a default behavior in v0.x (auto-exported unless disabled), the importer should either:
- Always add `environment: { TEAMOCIL: "1" }` unless `with_env_var: false`
- Or simply drop it, since it's an implementation detail of teamocil

### 6. `cmd_separator` (v0.x only)

**Verified**: `cmd_separator` exists in teamocil's v0.x at `lib/teamocil/layout/window.rb`. It's a per-window string (default `"; "`) used to join multiple pane commands before sending via `send-keys`. Removed in v1.x (hardcoded to `"; "`).

tmuxp sends commands individually (one `send_keys` per command), so this is irrelevant — the importer can safely ignore it.

## Code Issues in Current Importer

### Bug: Redundant Filter Loop

```python
# Lines 143-149 (current)
if "filters" in w:
    if "before" in w["filters"]:
        for _b in w["filters"]["before"]:
            window_dict["shell_command_before"] = w["filters"]["before"]
    if "after" in w["filters"]:
        for _b in w["filters"]["after"]:
            window_dict["shell_command_after"] = w["filters"]["after"]
```

The `for _b in` loops are pointless — they iterate over the list but set the same value each time. Should be:

```python
if "filters" in w:
    if "before" in w["filters"]:
        window_dict["shell_command_before"] = w["filters"]["before"]
    if "after" in w["filters"]:
        window_dict["shell_command_after"] = w["filters"]["after"]
```

### Bug: v1.x String Panes Cause TypeError

```python
# Lines 157-163 (current)
if "panes" in w:
    for p in w["panes"]:
        if "cmd" in p:       # TypeError if p is a string
            p["shell_command"] = p.pop("cmd")
```

If `p` is a string (v1.x shorthand), `"cmd" in p` will check for substring match in the string, not a dict key. This will either silently pass (if the command doesn't contain "cmd") or incorrectly match.

### Verified TODOs: `with_env_var` and `cmd_separator`

Listed in the importer's docstring TODOs (`importers.py:121-123`). Both verified as v0.x features (present in `0.4-stable` branch, removed in v1.x rewrite). `with_env_var` auto-exports `TEAMOCIL=1`; `cmd_separator` controls command joining. Since the importer targets v0.x, these are valid TODOs — but `cmd_separator` is irrelevant since tmuxp sends commands individually.

### Missing v0.x Features: `height` and `target`

Not mentioned in the importer TODOs but present in v0.x:
- `height` (pane): Percentage for vertical split (`split-window -p <height>`). Like `width`, silently dropped.
- `target` (pane): Target pane for split operation (`split-window -t <target>`). Not imported.

### Silent Drops

- `clear` is preserved but unused by tmuxp
- `width` is dropped with no user warning
- `shell_command_after` is set but unused by tmuxp

## Summary Table

| teamocil Feature | Import Status | Classification |
|---|---|---|
| `session:` wrapper (v0.x) | ✓ Handled | Difference |
| `name` → `session_name` | ✓ Handled | Difference |
| `root` → `start_directory` | ✓ Handled | Difference |
| Window `name` → `window_name` | ✓ Handled | Difference |
| Window `root` → `start_directory` | ✓ Handled | Difference |
| Window `layout` | ✓ Handled | Difference |
| `splits` → `panes` (v0.x) | ✓ Handled | Difference |
| Pane `cmd` → `shell_command` (v0.x) | ✓ Handled | Difference |
| `filters.before` → `shell_command_before` (v0.x) | ⚠ Bug (redundant loop) | Difference (needs fix) |
| Pane `commands` → `shell_command` (v1.x) | ✗ Missing | Difference (needs add) |
| String pane shorthand (v1.x) | ✗ Missing (causes error) | Difference (needs add) |
| Window `focus` (v1.x) | ✗ Missing | Difference (needs add) |
| Pane `focus` (v1.x) | ✗ Missing | Difference (needs add) |
| Window `options` (v1.x) | ✗ Missing | Difference (needs add) |
| `with_env_var` (v0.x) | ✗ Missing | Difference (v0.x only, can map to `environment`) |
| `filters.after` → `shell_command_after` | ⚠ Imported but unused | **Limitation** |
| Pane `width` (v0.x) | ⚠ Dropped silently | **Limitation** |
| Window `clear` (v0.x) | ⚠ Preserved but unused | **Limitation** |
| `cmd_separator` (v0.x) | ✗ Missing | Difference (v0.x only, irrelevant — tmuxp sends individually) |
| `height` (v0.x pane) | ✗ Missing | **Limitation** (like `width`, no per-pane sizing) |
| `target` (v0.x pane) | ✗ Missing | **Limitation** (no split targeting) |
| `--here` flag | N/A (runtime flag) | **Limitation** |
