# Feature Parity Plan

API limitations blocking full tmuxinator/teamocil parity.

## libtmux Limitations

### 1. No configurable tmux binary path
- **Blocker**: `shutil.which("tmux")` hardcoded in `common.py:602`
- **Blocks**: tmuxinator's `tmux_command` (wemux/byobu support)
- **Required**: Add `tmux_bin` parameter to Server

### 2. No pane title method
- **Blocker**: No `pane.set_title()` method exists
- **Blocks**: tmuxinator's named panes, `enable_pane_titles`
- **Required**: Add `set_title()` using `select-pane -T`

## tmuxp Limitations

### 1. Dead config keys (imported but ignored)
- **`socket_name`** — importer sets at line 51-52, `load_workspace()` ignores
- **`socket_path`** — no config key exists, CLI only
- **`config`** — importer extracts from `-f`, never read
- **`shell_command_after`** — teamocil importer sets, `trickle()` ignores
- **`shell_command`** (session-level) — importer sets from `pre`, never used
- **`clear`** — teamocil importer passes through, builder ignores

### 2. Missing config keys
- **`attach: false`** — only CLI `-d` exists
- **`synchronize`** — workaround via `options_after` but no sugar
- **Pane titles** — no `title`, `enable_pane_titles`, `pane_title_format` support
- **Shell hooks** — only Python plugin API, no shell commands in config

### 3. CLI gaps
- **`--debug`** — no dry-run mode
- **`--here`** — no reuse-current-window mode
- **`--no-shell-command-before`** — no skip pre commands
- **CLI arg passing** — no `tmuxp load config -- args`

### 4. Importer bugs blocking correct import
- `pre_window` alone silently ignored (only works with `pre`)
- `rvm` not handled (only `rbenv`)
- `startup_window`/`startup_pane` not mapped to `focus: true`
- teamocil v1.4.2 format not supported (`commands` vs `cmd`)
- String panes crash teamocil importer

## Implementation Notes

### Non-breaking additions

All changes can be additive:
- New config keys with sensible defaults (existing configs unchanged)
- New CLI flags that are optional
- API methods that don't change existing signatures
- `trickle()` can be extended to handle new keys

### Priority order

1. Fix dead config keys (no API changes, just read what's already there)
2. Add missing config keys (additive, defaults preserve behavior)
3. Fix importer bugs (improves compatibility, doesn't affect native configs)
4. Add CLI features (optional flags)
5. libtmux changes (requires coordination with libtmux releases)
