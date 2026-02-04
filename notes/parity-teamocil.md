# Teamocil Feature Parity Analysis

What teamocil (v1.4.2) has that tmuxp currently lacks, with import gap analysis and
WorkspaceBuilder requirements.

## Features teamocil has that tmuxp lacks

### A. Configuration Features

#### 1. `--here` flag (reuse current window)

Renames the current window instead of creating a new one. The first window in the config replaces the current window.

**Location**: `lib/teamocil/tmux/window.rb:67-73`

**tmuxp equivalent**: None. tmuxp always creates new windows.

#### 2. `--debug` flag (show tmux commands without executing)

Prints the tmux commands that would be run, without executing them.

**Location**: `lib/teamocil/layout.rb`

**tmuxp equivalent**: None.

#### 3. `--show` flag (display config without executing)

Prints the YAML config contents without loading the session.

**Location**: `lib/teamocil/layout.rb`

**tmuxp equivalent**: None (could `cat` the file).

#### 4. Optional session name

Session name is optional in teamocil — auto-generates a random name if omitted.

**Location**: `lib/teamocil/tmux/session.rb:8`

**tmuxp equivalent**: `session_name` is required. WorkspaceBuilder raises an error without it.

### B. Features teamocil has that tmuxp also has (parity exists)

| teamocil | tmuxp | Status |
|---|---|---|
| `windows[].options` (arbitrary `set-window-option`) | `windows[].options` | ✓ Equivalent |
| `windows[].focus: true` | `windows[].focus: true` | ✓ Equivalent |
| `panes[].focus: true` | `panes[].focus: true` | ✓ Equivalent |
| `layout` (preset + custom) | `layout` | ✓ Equivalent |
| `root` (window-level) | `start_directory` | ✓ Equivalent (different key name) |

---

## Syntax Differences

| teamocil | tmuxp | Notes |
|---|---|---|
| `name` (session) | `session_name` | Key rename |
| `windows[].name` | `windows[].window_name` | Key rename |
| `windows[].root` | `windows[].start_directory` | Key rename |
| `panes` as string `"vim"` | `panes[].shell_command: ["vim"]` | Shorthand expansion |
| `panes[].commands` (list) | `panes[].shell_command` (list) | Key rename |
| `splits` (v0.x) | `panes` | Key rename (legacy) |
| `panes[].cmd` (v0.x singular) | `panes[].shell_command` | Key rename (legacy) |
| `filters.before` (v0.x) | `shell_command_before` | Key rename (legacy) |
| `filters.after` (v0.x) | `shell_command_after` | Key rename (legacy) |

---

## Import Gaps (teamocil → tmuxp)

### CRITICAL: Importer targets OLD v0.x format

The current `import_teamocil` function (`src/tmuxp/workspace/importers.py:105-170`) targets teamocil's **old v0.x format**, NOT the current v1.4.2. Evidence:

- Uses `cmd` (singular) at line 159 — v1.4.2 uses `commands` (plural)
- Handles `filters` (lines 143-149) — removed in v1.0 rewrite
- Handles `clear` (line 140) — removed in v1.0
- Handles `splits` (lines 154-155) — renamed to `panes` in v1.0
- Test fixtures (`tests/fixtures/import_teamocil/`) all use old format with `cmd` key

### Currently handled (v0.x format)

| teamocil v0.x key | tmuxp mapping | Status |
|---|---|---|
| `session` wrapper | Unwrapped | ✓ |
| `name` | `session_name` | ✓ |
| `root` (session) | `start_directory` | ✓ |
| `windows[].name` | `window_name` | ✓ |
| `windows[].root` | `start_directory` | ✓ |
| `windows[].splits` | `panes` | ✓ |
| `panes[].cmd` | `shell_command` | ✓ |
| `windows[].layout` | `layout` | ✓ |
| `windows[].clear` | `clear` | ✓ (passed through) |
| `filters.before` | `shell_command_before` | ✓ |
| `filters.after` | `shell_command_after` | ✓ |
| `width` | Dropped | ✓ (silently removed) |

### Missing: v1.4.2 format support

| teamocil v1.4.2 key | Recommended tmuxp mapping | Notes |
|---|---|---|
| Pane as plain string (`- vim`) | `shell_command: ["vim"]` | Not handled — expects dict |
| `panes[].commands` (plural) | `shell_command` | Only `cmd` (singular) handled |
| `windows[].options` | `options` | Direct mapping, not implemented |
| `windows[].focus` | `focus: true` | Not explicitly mapped |
| `panes[].focus` | `focus: true` | Not explicitly mapped (may pass through implicitly) |
| Optional session name | Generate name or warn | tmuxp requires `session_name` |

### Format detection recommendation

Keep old v0.x support (mark as legacy), add v1.4.2 support alongside.

**Detection heuristic**:
- If panes contain `cmd` key → old v0.x format
- If panes contain `commands` key or are plain strings → v1.4.2 format
- If config has `filters`, `splits`, `clear`, `cmd_separator` → old v0.x format

### Code quality issues in current importer

1. **Mutating input**: Uses `dict.pop()` at lines 133, 152, 155, 160, 163 — destructively modifies the input dict.

2. **Assumes dict panes**: At line 158-163, iterates panes and checks `"cmd" in p` — will crash if `p` is a string (which is valid in both v0.x and v1.4.2).

3. **Assumes `name` key in windows**: Line 138 does `w["name"]` with no fallback — will KeyError if window has no `name` (valid in v1.4.2 where name is optional).

4. **Minimal test coverage**: 4 test fixtures + 4 multisession. All use old v0.x format. No tests for v1.4.2 format, focus, options, string panes, or missing names.

---

## WorkspaceBuilder Requirements for Full Teamocil Parity

Teamocil v1.4.2 is already well-covered by tmuxp's feature set. The main gaps are:

### 1. `--here` mode (reuse current window)

Instead of creating the first window, rename the current window and add panes to it.

**Implementation**: Similar to `--append` but for the first window only. The first window config renames the current window rather than creating a new one.

**Files**: `src/tmuxp/workspace/builder.py`, `src/tmuxp/cli/load.py`

### 2. Optional session name

Generate a name like `tmuxp-<random>` if `session_name` is `None` or missing.

**Files**: `src/tmuxp/workspace/builder.py` (validation step)

### 3. Update teamocil importer for v1.4.2

Add support for the modern teamocil format alongside the existing v0.x support:

- Handle pane strings (`- vim` → `{shell_command: ["vim"]}`)
- Handle `commands` (plural) in addition to `cmd` (singular)
- Map `options`, `focus` keys
- Handle optional window names
- Handle optional session names

**Files**: `src/tmuxp/workspace/importers.py`

### 4. Auto-detect config format

Same as tmuxinator parity (§WorkspaceBuilder Requirements in `parity-tmuxinator.md`):

Add `detect_format(config_dict) -> "tmuxp" | "tmuxinator" | "teamocil"` for transparent loading.

**teamocil detection heuristics**:
- Has `session.windows` wrapper
- Has `windows[].splits`
- Windows use `name` instead of `window_name`
- Panes use `commands` instead of `shell_command`
- Panes use `cmd` (v0.x)

**Files**: `src/tmuxp/workspace/importers.py` or new `src/tmuxp/workspace/detect.py`
