# Feature Parity Plan

API limitations blocking full tmuxinator/teamocil parity.

## libtmux Limitations

### 1. No configurable tmux binary path

- **Blocker**: `shutil.which("tmux")` hardcoded in 4 locations:
  - `src/libtmux/common.py:121` — `_rust_run_with_config()`
  - `src/libtmux/common.py:261` — `_rust_cmd_result()`
  - `src/libtmux/common.py:602` — `tmux_cmd.__init__()`
  - `src/libtmux/server.py:284` — `Server.raise_if_dead()`
- **Blocks**: tmuxinator's `tmux_command` (wemux/byobu support)
- **Required**: Add `tmux_bin` parameter to `Server.__init__()` and propagate to `tmux_cmd()`

### 2. No pane title method

- **Blocker**: No `Pane.set_title()` method exists in `src/libtmux/pane.py`
- **Note**: `pane_title` format was removed in tmux 3.1+ (comment at `src/libtmux/formats.py:70`), but `select-pane -T` still works for custom titles
- **Evidence**: `pane-title-changed` hook exists (`src/libtmux/hooks.py:19`) but no setter
- **Blocks**: tmuxinator's named panes, `enable_pane_titles`, `pane_title_format`
- **Required**: Add `Pane.set_title(title: str)` using `select-pane -T {title}`

### 3. Server already supports socket/config (not a blocker)

Server `__init__` at `src/libtmux/server.py:140-179` accepts:
- `socket_name` — maps to `tmux -L`
- `socket_path` — maps to `tmux -S`
- `config_file` — maps to `tmux -f`
- `colors` — 256 or 88

**Not a libtmux blocker** — tmuxp just needs to read these from config and pass them through.

---

## tmuxp Limitations

### 1. Dead config keys (imported but ignored)

Keys that importers set but `WorkspaceBuilder` never reads:

| Key | Set by | Location | Problem |
|-----|--------|----------|---------|
| `socket_name` | tmuxinator importer | `importers.py:51-52` | `load_workspace()` only accepts via CLI args (`cli/load.py:370`) |
| `socket_path` | — | N/A | No config key exists, CLI only (`cli/load.py:371`) |
| `config` | tmuxinator importer | `importers.py:36-49` | Extracted from `-f` flag, never read by builder |
| `shell_command_after` | teamocil importer | `importers.py:147-149` | `trickle()` only handles `shell_command_before` (`loader.py:245-256`) |
| `shell_command` (session) | tmuxinator importer | `importers.py:60` | Builder only reads window/pane level, not session |
| `clear` | teamocil importer | `importers.py:140-141` | Pass-through, builder ignores |
| `attach` | — | N/A | No config key, only CLI `-d` exists |

**trickle() behavior** (`loader.py:191-264`): Passes through unknown keys unchanged — they persist in the dict but are never consumed.

**WorkspaceBuilder keys** (`builder.py:250-313`): Only reads `session_name`, `start_directory`, `before_script`, `options`, `global_options`, `environment`, `windows`.

### 2. Missing config keys

| Feature | tmuxinator/teamocil | tmuxp status |
|---------|---------------------|--------------|
| `attach: false` | Config key | CLI `-d` only |
| `synchronize` | First-class key | Workaround: `options_after: {synchronize-panes: on}` |
| `enable_pane_titles` | Session-level | Not supported |
| `pane_title_format` | Session-level | Not supported |
| `pane_title_position` | Session-level | Not supported |
| Per-pane `title` | Named panes | Not supported |
| `on_project_start` | Shell command hook | Only Python plugin API |
| `on_project_exit` | Shell command hook | Only Python plugin API |

### 3. CLI gaps

| Feature | tmuxinator/teamocil | tmuxp |
|---------|---------------------|-------|
| `--debug` | Dry-run mode | Not implemented |
| `--here` | Reuse current window | Not implemented |
| `--no-pre-window` | Skip pre commands | Not implemented (only `--no-startup` for shell.py) |
| `config -- args` | CLI argument passing | Not implemented |

### 4. Importer bugs blocking correct import

**tmuxinator importer** (`importers.py:8-102`):

| Bug | Location | Impact |
|-----|----------|--------|
| `pre_window` alone ignored | Line 59: requires both `pre` AND `pre_window` | Common case silently broken |
| `rvm` not handled | Only `rbenv` at lines 72-77 | rvm users get no shell setup |
| `startup_window`/`startup_pane` not mapped | Not implemented | Should set `focus: true` on matching window/pane |
| Named panes lose title | Lines extracts commands, drops key name | Pane titles discarded |
| Loop reassignment bug | Lines 80-81: reassigns loop variable | Only works for single-key window hashes |
| Input mutation | `dict.pop()` throughout | Caller's dict is destroyed |

**teamocil importer** (`importers.py:105-170`):

| Bug | Location | Impact |
|-----|----------|--------|
| v1.4.2 format not supported | Uses `cmd` not `commands` | Modern teamocil configs fail |
| String panes crash | Line 158-159: `if "cmd" in p` | TypeError when `p` is string |
| Missing window name | Line 138: `w["name"]` | KeyError when name optional |
| `commands` (plural) not handled | Only checks `cmd` | v1.4.2 pane commands ignored |
| Unused loop in filters | Lines 145-146, 148-149 | Pointless iteration |

---

## Implementation Plan

### Phase 1: Fix dead config keys (no API changes)

Read existing keys in `load_workspace()` and pass to `Server()`:

```python
# cli/load.py, around line 369
socket_name = args.socket_name or expanded_workspace.get("socket_name")
socket_path = args.socket_path or expanded_workspace.get("socket_path")
config_file = args.tmux_config_file or expanded_workspace.get("config")
```

**Effort**: Small change, CLI args override config, backwards compatible.

### Phase 2: Add missing config keys

1. **`attach: false`**: Read in `load_workspace()`, merge with CLI `-d` flag
2. **`synchronize`**: Sugar in `loader.expand()` that maps to `options_after`
3. **`shell_command_after`**: Add to `trickle()` alongside `shell_command_before`

**Effort**: Additive changes to loader/builder, existing configs unchanged.

### Phase 3: Fix importer bugs

1. **tmuxinator**: Handle `pre_window` independently, add `rvm` support, map `startup_*` to focus
2. **teamocil**: Add v1.4.2 format detection, handle string panes, handle `commands` (plural)

**Effort**: Improves compatibility, doesn't affect native tmuxp configs.

### Phase 4: Add CLI features

1. **`--debug`**: Print tmux commands without executing
2. **`--here`**: Rename current window instead of creating new
3. **`--no-shell-command-before`**: Skip pre commands
4. **`config -- args`**: Pre-process sys.argv to extract args after `--`

**Effort**: New optional flags, no behavior change for existing usage.

### Phase 5: libtmux changes (requires coordination)

1. **`tmux_bin` parameter**: Add to `Server.__init__`, propagate to `tmux_cmd()`
2. **`Pane.set_title()`**: Add method using `select-pane -T`

**Effort**: Requires libtmux release, then tmuxp update.

---

## Priority Order

1. **Fix dead config keys** — No API changes, just read what's already there
2. **Add missing config keys** — Additive, defaults preserve behavior
3. **Fix importer bugs** — Improves compatibility, doesn't affect native configs
4. **Add CLI features** — Optional flags
5. **libtmux changes** — Requires coordination with libtmux releases

---

## File Reference

| Component | File | Key Lines |
|-----------|------|-----------|
| WorkspaceBuilder | `src/tmuxp/workspace/builder.py` | 250-313 (session keys), 329-344 (focus) |
| trickle() | `src/tmuxp/workspace/loader.py` | 191-264 |
| expand() | `src/tmuxp/workspace/loader.py` | 168-171 |
| load_workspace() | `src/tmuxp/cli/load.py` | 255-374, esp. 369-374 |
| tmuxinator importer | `src/tmuxp/workspace/importers.py` | 8-102 |
| teamocil importer | `src/tmuxp/workspace/importers.py` | 105-170 |
| Server init | `~/work/python/libtmux/src/libtmux/server.py` | 140-179 |
| tmux binary lookup | `~/work/python/libtmux/src/libtmux/common.py` | 121, 261, 602 |
| Pane class | `~/work/python/libtmux/src/libtmux/pane.py` | No set_title method |
