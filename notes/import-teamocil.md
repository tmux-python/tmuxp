# Teamocil Import Behavior

Analysis of `import_teamocil()` in `src/tmuxp/workspace/importers.py:105-170`.

## CRITICAL: Targets OLD v0.x format only

The current importer was written for teamocil's **old v0.x format**, NOT the current v1.4.2. Evidence:

| Feature | Importer handles | teamocil v1.4.2 uses |
|---------|------------------|----------------------|
| Pane commands | `cmd` (singular) | `commands` (plural) |
| `filters.before/after` | ✓ handled | Removed in v1.0 |
| `clear` | ✓ handled | Removed in v1.0 |
| `splits` | ✓ → `panes` | Renamed to `panes` in v1.0 |
| Pane as string | ✗ crashes | Valid syntax |

The v1.0 rewrite (2015) changed the schema significantly. See [teamocil CHANGELOG](https://github.com/remi/teamocil/blob/main/CHANGELOG.md).

---

## v0.x Syntax (Currently Handled)

### Key renames

| teamocil v0.x | tmuxp | Lines |
|---------------|-------|-------|
| `session` wrapper | Unwrapped | 127-128 |
| `name` | `session_name` | 130 |
| `root` (session) | `start_directory` | 132-133 |
| `windows[].name` | `window_name` | 138 |
| `windows[].root` | `start_directory` | 151-152 |
| `windows[].splits` | `panes` | 154-155 |
| `windows[].layout` | `layout` | 166-167 |
| `panes[].cmd` | `shell_command` | 159-160 |
| `clear` | `clear` | 140-141 (pass-through, but **dead data** — WorkspaceBuilder ignores it) |
| `filters.before` | `shell_command_before` | 144-146 |
| `filters.after` | `shell_command_after` | 147-149 (**dead data** — tmuxp only supports `shell_command_before`) |
| `width` | Dropped | 161-163 (silently removed) |

### Pass-through keys

These keys pass through unchanged:
- `layout` (line 166-167)
- `clear` (line 140-141) — though tmuxp may not support it

---

## v1.4.2 Syntax (NOT Handled)

### Missing key mappings

| teamocil v1.4.2 | Should map to | Notes |
|-----------------|---------------|-------|
| `panes[].commands` | `shell_command` | Only `cmd` (v0.x) is handled |
| `windows[].options` | `options` | Direct mapping, not implemented |
| `windows[].focus` | `focus: true` | NOT handled; only specific keys are copied to `window_dict` |
| `panes[].focus` | `focus: true` | Passes through implicitly (pane dicts kept intact) |

### Pane as string (crashes)

teamocil v1.4.2 supports panes as plain strings:

```yaml
panes:
  - vim
  - rails server
```

The v1.4.2 source handles this at `lib/teamocil/tmux/window.rb:14`:

```ruby
pane = { commands: [pane] } if pane.is_a?(String)
```

But the tmuxp importer assumes panes are dicts (line 158-163):

```python
if "panes" in w:
    for p in w["panes"]:
        if "cmd" in p:  # TypeError if p is a string!
```

**Result**: `TypeError: argument of type 'str' is not iterable`

### Optional session name

teamocil v1.4.2 auto-generates session names (`lib/teamocil/tmux/session.rb:8`):

```ruby
self.name = "teamocil-session-#{rand(1_000_000)}" unless name
```

The importer sets `session_name` to `None` (line 130), which causes tmuxp's `WorkspaceBuilder` to raise an error.

---

## Importer Bugs

### 1. KeyError on missing window name (line 138)

```python
for w in workspace_dict["windows"]:
    window_dict = {"window_name": w["name"]}  # KeyError if no "name"!
```

teamocil v1.4.2 allows unnamed windows. The importer crashes.

**Fix**: Use `w.get("name")` and handle `None`.

### 2. TypeError on string panes (line 158-159)

```python
if "panes" in w:
    for p in w["panes"]:
        if "cmd" in p:  # TypeError when p is a string
```

**Fix**: Check `isinstance(p, str)` first and convert to dict.

### 3. Mutating input dict (throughout)

Uses `dict.pop()` at lines 133, 152, 155, 160, 163 — destructively modifies the input dict.

### 4. Unused loop variable in filters (lines 145-146, 148-149)

```python
if "before" in w["filters"]:
    for _b in w["filters"]["before"]:  # loop does nothing
        window_dict["shell_command_before"] = w["filters"]["before"]
```

The loop iterates but just reassigns the same value each time. The loop is pointless — likely a copy-paste error. Should be:

```python
if "before" in w["filters"]:
    window_dict["shell_command_before"] = w["filters"]["before"]
```

### 5. `commands` (plural) not handled

The importer only checks for `cmd` (v0.x singular). teamocil v1.4.2 uses `commands` (plural):

```yaml
# v0.x
panes:
  - cmd: "vim"

# v1.4.2
panes:
  - commands:
      - vim
      - rails server
```

---

## Test Fixture Analysis

All test fixtures use the **old v0.x format**:

### test1.yaml
- Basic window with `cmd` (string)
- `cmd` as list: `["pwd", "ls -la"]`

### test2.yaml
- Multiple windows, simple `cmd: "pwd"`

### test3.yaml
- `filters.before/after` (v0.x only)
- `focus: true` on pane
- `cmd` as list of commands

### test4.yaml
- ERB template syntax (not related to import)

### layouts.yaml
- `session` wrapper (v0.x)
- `splits` key (v0.x, renamed to `panes` in v1.0)
- `clear: true` (v0.x)
- `cmd_separator`, `with_env_var` (v0.x)
- `width`, `target` on panes (v0.x)

**No v1.4.2 format tests exist.**

---

## Format Detection Heuristics

To distinguish v0.x from v1.4.2:

| Indicator | Format |
|-----------|--------|
| Has `session` wrapper | v0.x |
| Has `splits` key | v0.x |
| Has `filters` key | v0.x |
| Has `clear` key | v0.x |
| Has `cmd_separator` key | v0.x |
| Panes use `cmd` (singular) | v0.x |
| Panes use `commands` (plural) | v1.4.2 |
| Panes are plain strings | v1.4.2 (also valid in v0.x but rare) |
| Windows have `options` key | v1.4.2 |

---

## Summary

| Category | Count |
|----------|-------|
| v0.x keys handled correctly | 9 |
| v0.x keys → dead data | 2 (`clear`, `filters.after` → `shell_command_after`) |
| v1.4.2 keys not handled | 4 (`commands`, `options`, window `focus`, string panes) |
| Code bugs | 5 |
| Test coverage | v0.x only, no v1.4.2 tests |

### Recommendation

Keep v0.x support (mark as legacy), add v1.4.2 support alongside with proper format detection.
