# Parity Implementation Plan

*Last updated: 2026-02-08*
*Based on: parity-tmuxinator.md, parity-teamocil.md, import-tmuxinator.md, import-teamocil.md*

## libtmux Limitations

### L1. No `Pane.set_title()` Method

- **Blocker**: libtmux has no method wrapping `select-pane -T <title>`. The `pane_title` format variable is excluded from libtmux's bulk format queries (`formats.py:70`, commented out with note "removed in 3.1+"), but this is a libtmux-side exclusion — tmux itself still supports both `#{pane_title}` (in `format.c:205`) and `select-pane -T` (added in tmux 2.6). libtmux already knows about the display options (`pane_border_status`, `pane_border_format` in `constants.py:163-173`) but has no setter for the title itself.
- **Blocks**: Pane titles (tmuxinator feature: named pane syntax `pane_name: command` → `select-pane -T`). Also blocks `enable_pane_titles`, `pane_title_position`, `pane_title_format` session-level config.
- **Required**: Add `Pane.set_title(title: str)` method that calls `self.cmd("select-pane", "-T", title)`. This is a simple wrapper — `Pane.cmd()` already exists (`pane.py:177`) and `select-pane` is already used for `Pane.select()` (`pane.py:601`).
- **Non-breaking**: Pure addition, no existing API changes.

### L2. Hardcoded tmux Binary Path

- **Blocker**: `shutil.which("tmux")` is hardcoded in two independent code paths:
  - `common.py:252` — `tmux_cmd.__init__()`, the class through which all libtmux commands flow (called by `Server.cmd()` at `server.py:311`)
  - `server.py:223` — `Server.raise_if_dead()`, a separate code path that calls `subprocess.check_call()` directly
  There is no way to use a custom tmux binary (wemux, byobu, or custom-built tmux).
- **Blocks**: Wemux support (tmuxinator `tmux_command: wemux`). Also blocks CI/container use with non-standard tmux locations.
- **Required**: Add optional `tmux_bin` parameter to `Server.__init__()` that propagates to `tmux_cmd`. Both code paths must be updated. Default remains `shutil.which("tmux")`.
- **Non-breaking**: Optional parameter with backward-compatible default. Existing code is unaffected.

### L3. No Dry-Run / Command Preview Mode

- **Blocker**: `tmux_cmd` (`common.py:252-296`) always executes commands. Debug logging exists (`logger.debug` at line 291) but only logs stdout after execution, not the command being sent. There is no facility to collect commands without executing them.
- **Blocks**: `--debug` / dry-run mode (both tmuxinator and teamocil have this). tmuxinator generates a bash script that can be previewed; teamocil's `--debug` outputs the tmux command list.
- **Required**: Either (a) add a `dry_run` flag to `tmux_cmd` that collects commands instead of executing, or (b) add pre-execution logging at DEBUG level that logs the full command before `subprocess.run()`. Option (b) is simpler and doesn't change behavior.
- **Non-breaking**: Logging change only. tmuxp would implement the user-facing `--debug` flag by capturing log output.
- **Note**: Since tmuxp uses libtmux API calls (not command strings), a true dry-run would require a recording layer in `WorkspaceBuilder` that logs each API call. This is architecturally different from tmuxinator/teamocil's approach and may not be worth full parity.

### L4. Available APIs (No Blockers)

These libtmux APIs already exist and do NOT need changes:

| API | Location | Supports |
|---|---|---|
| `Session.rename_session(name)` | `session.py:412` | teamocil session rename mode |
| `Window.rename_window(name)` | `window.py:462` | teamocil `--here` flag |
| `Pane.resize(height, width)` | `pane.py:217` | teamocil v0.x pane `width` |
| `Pane.send_keys(cmd, enter)` | `pane.py:423` | All command sending |
| `Pane.select()` | `pane.py:577` | Pane focus |
| `Window.set_option(key, val)` | `options.py:578` (OptionsMixin) | `synchronize-panes`, window options |
| `Session.set_hook(hook, cmd)` | `hooks.py:111` (HooksMixin) | Lifecycle hooks (`client-detached`, etc.) |
| `Session.set_option(key, val)` | `options.py:578` (OptionsMixin) | `pane-border-status`, `pane-border-format` |
| `HooksMixin` on Session/Window/Pane | `session.py:55`, `window.py:56`, `pane.py:51` | All entities inherit hooks |

## tmuxp Limitations

### T1. No `synchronize` Config Key

- **Blocker**: `WorkspaceBuilder` (`builder.py`) does not check for a `synchronize` key on window configs. The key is silently ignored if present.
- **Blocks**: Pane synchronization (tmuxinator `synchronize: true/before/after`).
- **Required**: Add `synchronize` handling in `builder.py`. For `before`/`true`: call `window.set_option("synchronize-panes", "on")` before pane commands are sent. For `after`: call it in `config_after_window()`. For `false`/omitted: no action.
- **Insertion point**: In `build()` around line 320 (after `on_window_create` plugin hook, before `iter_create_panes()` loop) for `before`/`true`. In `config_after_window()` around line 565 for `after`. Note: in tmux 3.2+ (tmuxp's minimum), `synchronize-panes` is a dual-scope option (window|pane, `options-table.c:1423`). Setting it at window level via `window.set_option()` makes all panes inherit it, including those created later by split.
- **Non-breaking**: New optional config key. Existing configs are unaffected.

### T2. No Pane Title Config Key

- **Blocker**: `WorkspaceBuilder` has no handling for pane `title` key or session-level `enable_pane_titles` / `pane_title_position` / `pane_title_format`.
- **Blocks**: Pane titles (tmuxinator named pane syntax).
- **Required**:
  1. Session-level: set `pane-border-status` and `pane-border-format` options via `session.set_option()` in `build()` alongside other session options (lines 303-309).
  2. Pane-level: call `pane.cmd("select-pane", "-T", title)` after commands are sent in `iter_create_panes()`, before focus handling (around line 535). Requires L1 (libtmux `set_title()`), or can use `pane.cmd()` directly.
- **Config keys**: `enable_pane_titles: true`, `pane_title_position: top`, `pane_title_format: "..."` (session-level). `title: "my-title"` (pane-level).
- **Non-breaking**: New optional config keys.

### T3. No `shell_command_after` Config Key

- **Blocker**: The teamocil importer produces `shell_command_after` on the **window** dict (from `filters.after`, `importers.py:149`), but `WorkspaceBuilder` never reads it. The `trickle()` function in `loader.py` has no logic for it either.
- **Blocks**: teamocil v0.x `filters.after` — commands run after all pane commands in a window.
- **Required**: Add handling in `config_after_window()` (around line 565) or in `build()` after the `iter_create_panes()` loop (around line 331). Read `window_config.get("shell_command_after", [])` and send each command to every pane via `pane.send_keys()`. Note: this is a **window-level** key set by the teamocil importer, not per-pane.
- **Non-breaking**: New optional config key.

### T4. No Session Rename Mode / `--here` CLI Flag

- **Blocker**: `tmuxp load` (`cli/load.py`) has no `--here` flag. `WorkspaceBuilder.iter_create_windows()` always creates new windows via `session.new_window()` (line 406). Additionally, teamocil's session rename mode (rename current session instead of creating new) is partially covered by tmuxp's `--append` flag, but `--append` does not rename the session.
- **Blocks**: teamocil `--here` (reuse current window for first window) and teamocil session rename mode.
- **Required**:
  1. Add `--here` flag to `cli/load.py` (around line 516, near `--append`).
  2. Pass `here=True` through to `WorkspaceBuilder.build()`.
  3. In `iter_create_windows()`, when `here=True` and first window: use `window.rename_window(name)` instead of `session.new_window()`, and send `cd <root>` via `pane.send_keys()` for directory change.
  4. Adjust `first_window_pass()` logic (line 584).
  5. For session rename: when `--here` is used, also call `session.rename_session(name)` (line 262 area in `build()`).
- **Depends on**: libtmux `Window.rename_window()` and `Session.rename_session()` (both already exist, L4).
- **Non-breaking**: New optional CLI flag.

### T5. No `stop` / `kill` CLI Command

- **Blocker**: tmuxp has no `stop` command. The CLI modules (`cli/__init__.py`) only register: `load`, `freeze`, `ls`, `search`, `shell`, `convert`, `import`, `edit`, `debug-info`.
- **Blocks**: tmuxinator `stop` / `stop-all` — kill session with cleanup hooks.
- **Required**: Add `tmuxp stop <session>` command. Implementation: find session by name via `server.sessions`, call `session.kill()`. For hook support, run `on_project_stop` hook before kill.
- **Non-breaking**: New CLI command.

### T6. No Lifecycle Hook Config Keys

- **Blocker**: tmuxp's plugin system (`plugin.py:216-292`) has 5 hooks: `before_workspace_builder`, `on_window_create`, `after_window_finished`, `before_script`, `reattach`. These are Python plugin hooks, not config-driven shell command hooks. There are no config keys for `on_project_start`, `on_project_exit`, etc.
- **Blocks**: tmuxinator lifecycle hooks (`on_project_start`, `on_project_first_start`, `on_project_restart`, `on_project_exit`, `on_project_stop`).
- **Required**: Add config-level hook keys. Mapping:
  - `on_project_start` → run shell command at start of `build()`, before `before_script`
  - `on_project_first_start` → already partially covered by `before_script`
  - `on_project_restart` → run when reattaching (currently only plugin `reattach()` hook)
  - `on_project_exit` → use tmux `set-hook client-detached` via `session.set_hook()` (libtmux L4)
  - `on_project_stop` → run in new `tmuxp stop` command (T5)
- **Depends on**: T5 for `on_project_stop`.
- **Non-breaking**: New optional config keys.

### T7. No `--no-shell-command-before` CLI Flag

- **Blocker**: `tmuxp load` has no flag to skip `shell_command_before`. The `trickle()` function (`loader.py:245-256`) always prepends these commands.
- **Blocks**: tmuxinator `--no-pre-window` — skip per-pane pre-commands for debugging.
- **Required**: Add `--no-shell-command-before` flag to `cli/load.py`. When set, clear `shell_command_before` from all levels before calling `trickle()`.
- **Non-breaking**: New optional CLI flag.

### T8. No Config Templating

- **Blocker**: tmuxp has no user-defined variable interpolation. Environment variable expansion (`$VAR` via `os.path.expandvars()`) already works in most config values — `session_name`, `window_name`, `start_directory`, `before_script`, `environment`, `options`, `global_options` (see `loader.py:108-160`). But there is no way to pass custom `key=value` variables at load time.
- **Blocks**: tmuxinator ERB templating (`<%= @settings["key"] %>`).
- **Required**: Add a Jinja2 or Python `string.Template` pass before YAML parsing. Allow `key=value` CLI args to set template variables. This is a significant architectural addition.
- **Non-breaking**: Opt-in feature, existing configs are unaffected.

### T9. No `--debug` / Dry-Run CLI Flag

- **Blocker**: `tmuxp load` has no dry-run mode. Since tmuxp uses libtmux API calls rather than generating command strings, there's no natural command list to preview.
- **Blocks**: tmuxinator `debug` and teamocil `--debug` / `--show`.
- **Required**: Either (a) add a recording proxy layer around libtmux calls that logs what would be done, or (b) add verbose logging that shows each tmux command before execution (depends on L3).
- **Non-breaking**: New optional CLI flag.

### T10. Missing Config Management Commands

- **Blocker**: tmuxp only has `edit`. Missing: `new` (create from template), `copy` (duplicate config), `delete` (remove config with confirmation).
- **Blocks**: tmuxinator `new`, `copy`, `delete`, `implode` commands.
- **Required**: Add CLI commands. These are straightforward file operations.
- **Non-breaking**: New CLI commands.

## Dead Config Keys

Keys produced by importers but silently ignored by the builder:

| Key | Producer | Importer Line | Builder Handling | Issue |
|---|---|---|---|---|
| `shell_command` (session-level) | tmuxinator importer | `importers.py:60` | Not a valid session key | **Bug**: `pre` commands lost when both `pre` and `pre_window` exist |
| `config` | tmuxinator importer | `importers.py:37,44` | Never read | Dead data — extracted `-f` path goes nowhere |
| `socket_name` | tmuxinator importer | `importers.py:52` | Never read | Dead data — CLI uses `-L` flag |
| `clear` | teamocil importer | `importers.py:141` | Never read | Dead data — tmuxp has no clear support |
| `shell_command_after` | teamocil importer | `importers.py:149` | Never read | Dead data — tmuxp has no after-command support |

## Importer Bugs (No Builder Changes Needed)

### I1. tmuxinator `pre` + `pre_window` Mapping Bug

- **Bug**: When both `pre` and `pre_window` exist (`importers.py:59-65`):
  1. `pre` maps to `shell_command` (line 60) — invalid session-level key, silently ignored by builder. The `pre` commands are lost.
  2. The `isinstance` check on line 62 tests `workspace_dict["pre"]` type to decide how to wrap `workspace_dict["pre_window"]` — it should check `pre_window`'s type, not `pre`'s. If `pre` is a list but `pre_window` is a string, `pre_window` won't be wrapped in a list.
- **Correct mapping**: `pre` → `before_script` (session-level, runs once before windows). `pre_window` → `shell_command_before` (per-pane).
- **Note**: `before_script` expects a file path or command (executed via `subprocess.Popen` after `shlex.split()` in `util.py:27-32`), not inline shell commands. For inline commands, either write a temp script, or add an `on_project_start` config key (T6).

### I2. tmuxinator `cli_args` / `tmux_options` Fragile Parsing

- **Bug**: `str.replace("-f", "").strip()` (`importers.py:41,48`) matches `-f` as a substring anywhere in the string. A path like `/opt/foobar` would be corrupted. Also ignores `-L` (socket name) and `-S` (socket path) flags.
- **Fix**: Use proper argument parsing (e.g., `shlex.split()` + iterate to find `-f` flag and its value).

### I3. teamocil Redundant Filter Loops

- **Bug**: `for _b in w["filters"]["before"]:` loops (`importers.py:145-149`) iterate N times but set the same value each time.
- **Fix**: Replace with direct assignment.

### I4. teamocil v1.x Format Not Supported

- **Bug**: Importer assumes v0.x format. String panes cause incorrect behavior (`"cmd" in "git status"` checks substring, not dict key). `commands` key (v1.x) not mapped.
- **Fix**: Add format detection. Handle string panes, `commands` key, `focus`, and `options`.

### I5. tmuxinator Missing Keys

Not imported but translatable:
- `rvm` → `shell_command_before: ["rvm use {value}"]`
- `pre_tab` → `shell_command_before` (deprecated predecessor to `pre_window`)
- `startup_window` → find matching window, set `focus: true`
- `startup_pane` → find matching pane, set `focus: true`
- `on_project_first_start` → `before_script` (only if value is a single command or script path; multi-command strings joined by `;` won't work since `before_script` uses `Popen` without `shell=True`)
- `socket_path` → warn user to use CLI `-S` flag
- `attach: false` → warn user to use CLI `-d` flag

### I6. teamocil Missing Keys (v1.x)

Not imported but translatable (same key names in tmuxp):
- `commands` → `shell_command`
- `focus` (window) → `focus` (pass-through)
- `focus` (pane) → `focus` (pass-through)
- `options` (window) → `options` (pass-through)
- String pane shorthand → `shell_command: [command]`

### I7. Stale Importer TODOs

`importers.py:121,123` lists `with_env_var` and `cmd_separator` as TODOs (with `clear` at line 122 in between), but neither `with_env_var` nor `cmd_separator` exists in teamocil v1.4.2 source. These are stale references from ~2013 and should be removed.

## Implementation Priority

### Phase 1: Import Fixes (No Builder/libtmux Changes)

These fix existing bugs and add missing translations without touching the builder:

1. **I3**: Fix redundant filter loops (teamocil)
2. **I4**: Add v1.x teamocil format support
3. **I6**: Import teamocil v1.x keys (`commands`, `focus`, `options`, string panes)
4. **I5**: Import missing tmuxinator keys (`rvm`, `pre_tab`, `startup_window`, `startup_pane`)
5. **I1**: Fix `pre`/`pre_window` mapping (tmuxinator)
6. **I2**: Fix `cli_args` parsing (tmuxinator)
7. **I7**: Remove stale TODOs

### Phase 2: Builder Additions (tmuxp Only)

These add new config key handling to the builder:

1. **T1**: `synchronize` config key — straightforward `set_option()` call
2. **T3**: `shell_command_after` config key — straightforward `send_keys()` loop
3. **T4**: `--here` CLI flag — moderate complexity, uses existing libtmux APIs

### Phase 3: libtmux Additions

These require changes to the libtmux package:

1. **L1**: `Pane.set_title()` — simple wrapper, needed for T2
2. **T2**: Pane title config keys — depends on L1

### Phase 4: New CLI Commands

3. **T5**: `tmuxp stop` command
4. **T10**: `tmuxp new`, `tmuxp copy`, `tmuxp delete` commands

### Phase 5: Larger Features (Nice-to-Have)

5. **T6**: Lifecycle hook config keys — complex, needs design
6. **T7**: `--no-shell-command-before` flag — simple
7. **T8**: Config templating — significant architectural addition
8. **T9**: `--debug` / dry-run mode — depends on L3
9. **L2**: Custom tmux binary — requires libtmux changes
