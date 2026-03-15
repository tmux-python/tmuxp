# Parity Implementation Plan

*Last updated: 2026-03-15*
*Based on: parity-tmuxinator.md, parity-teamocil.md, import-tmuxinator.md, import-teamocil.md*

## libtmux Limitations

### L1. No `Pane.set_title()` Method — **RESOLVED in libtmux v0.55.0**

**Status**: `Pane.set_title(title)` added at `pane.py:834-859`. Unblocks T2.

- ~~**Blocker**: libtmux has no method wrapping `select-pane -T <title>`.~~
- ~~**Blocks**: Pane titles (tmuxinator feature: named pane syntax `pane_name: command` → `select-pane -T`). Also blocks `enable_pane_titles`, `pane_title_position`, `pane_title_format` session-level config.~~
- ~~**Required**: Add `Pane.set_title(title: str)` method that calls `self.cmd("select-pane", "-T", title)`.~~
- **Non-breaking**: Pure addition, no existing API changes.

### L2. Hardcoded tmux Binary Path — **RESOLVED in libtmux v0.55.0**

**Status**: `Server(tmux_bin=...)` added at `server.py:142`. Unblocks tmuxinator `tmux_command`.

- ~~**Blocker**: `shutil.which("tmux")` is hardcoded in two independent code paths.~~
- ~~**Blocks**: Wemux support (tmuxinator `tmux_command: wemux`). Also blocks CI/container use with non-standard tmux locations.~~
- ~~**Required**: Add optional `tmux_bin` parameter to `Server.__init__()` that propagates to `tmux_cmd`.~~
- **Non-breaking**: Optional parameter with backward-compatible default. Existing code is unaffected.

### L3. No Dry-Run / Command Preview Mode — **RESOLVED in libtmux v0.55.0**

**Status**: Pre-execution `logger.debug` added at `common.py:263-268`. Unblocks T9.

- ~~**Blocker**: `tmux_cmd` always executes commands with no pre-execution logging.~~
- ~~**Blocks**: `--debug` / dry-run mode (both tmuxinator and teamocil have this).~~
- ~~**Required**: Add pre-execution logging at DEBUG level that logs the full command before `subprocess.run()`.~~
- **Non-breaking**: Logging change only. tmuxp would implement the user-facing `--debug` flag by capturing log output.
- **Note**: Since tmuxp uses libtmux API calls (not command strings), a true dry-run would require a recording layer in `WorkspaceBuilder` that logs each API call. This is architecturally different from tmuxinator/teamocil's approach and may not be worth full parity.

### L4. Available APIs (No Blockers)

These libtmux APIs already exist and do NOT need changes:

| API | Location | Supports |
|---|---|---|
| `Session.rename_session(name)` | `session.py:422` | teamocil session rename mode |
| `Window.rename_window(name)` | `window.py:462` | teamocil `--here` flag |
| `Pane.resize(height, width)` | `pane.py:217` | teamocil v0.x pane `width` |
| `Pane.send_keys(cmd, enter)` | `pane.py:423` | All command sending |
| `Pane.select()` | `pane.py:586` | Pane focus |
| `Window.set_option(key, val)` | `options.py:593` (OptionsMixin) | `synchronize-panes`, window options |
| `Session.set_hook(hook, cmd)` | `hooks.py:118` (HooksMixin) | Lifecycle hooks (`client-detached`, etc.) |
| `Session.set_option(key, val)` | `options.py:593` (OptionsMixin) | `pane-border-status`, `pane-border-format` |
| `HooksMixin` on Session/Window/Pane | `session.py:55`, `window.py:56`, `pane.py:51` | All entities inherit hooks |
| `HooksMixin.set_hooks()` (bulk) | `hooks.py:437` | Efficient multi-hook setup (dict/list input) |
| `Session.set_environment(key, val)` | `common.py:63` (EnvironmentMixin) | Session-level env vars (teamocil `with_env_var`) |
| `Pane.clear()` | `pane.py:869` | Sends `reset` to clear pane (teamocil `clear`) |
| `Pane.reset()` | `pane.py:874` | `send-keys -R \; clear-history` (full reset) |
| `Pane.split(target=...)` | `pane.py:634` | Split targeting (teamocil v0.x `target`) |

## tmuxp Limitations

### T1. No `synchronize` Config Key

- **Blocker**: `WorkspaceBuilder` (`builder.py`) does not check for a `synchronize` key on window configs. The key is silently ignored if present.
- **Blocks**: Pane synchronization (tmuxinator `synchronize: true/before/after`). Note: tmuxinator deprecates `true`/`before` in favor of `after` (`project.rb:21-29`), but all three values still function. The import should honor original semantics of each value.
- **Required**: Add `synchronize` handling in `builder.py`. For `before`/`true`: call `window.set_option("synchronize-panes", "on")` before pane commands are sent. For `after`: call it in `config_after_window()`. For `false`/omitted: no action.
- **Insertion point**: In `build()` around line 541 (after `on_window_create` plugin hook, before `iter_create_panes()` loop) for `before`/`true`. In `config_after_window()` around line 822 for `after`. Note: in tmux 3.2+ (tmuxp's minimum), `synchronize-panes` is a dual-scope option (window|pane, `options-table.c:1423`). Setting it at window level via `window.set_option()` makes all panes inherit it, including those created later by split.
- **Non-breaking**: New optional config key. Existing configs are unaffected.

### T2. No Pane Title Config Key

- **Blocker**: `WorkspaceBuilder` has no handling for pane `title` key or session-level `enable_pane_titles` / `pane_title_position` / `pane_title_format`.
- **Blocks**: Pane titles (tmuxinator named pane syntax).
- **Required**:
  1. Session-level: set `pane-border-status` and `pane-border-format` options via `session.set_option()` in `build()` alongside other session options (lines 529-539).
  2. Pane-level: call `pane.cmd("select-pane", "-T", title)` after commands are sent in `iter_create_panes()`, before focus handling (around line 816). Requires L1 (libtmux `set_title()`), or can use `pane.cmd()` directly.
- **Config keys**: `enable_pane_titles: true`, `pane_title_position: top`, `pane_title_format: "..."` (session-level). `title: "my-title"` (pane-level).
- **Non-breaking**: New optional config keys.

### T3. No `shell_command_after` Config Key

- **Blocker**: The teamocil importer produces `shell_command_after` on the **window** dict (from `filters.after`, `importers.py:149`), but `WorkspaceBuilder` never reads it. The `trickle()` function in `loader.py` has no logic for it either.
- **Blocks**: teamocil v0.x `filters.after` — commands run after all pane commands in a window.
- **Required**: Add handling in `config_after_window()` (around line 822) or in `build()` after the `iter_create_panes()` loop. Read `window_config.get("shell_command_after", [])` and send each command to every pane via `pane.send_keys()`. Note: this is a **window-level** key set by the teamocil importer, not per-pane.
- **Non-breaking**: New optional config key.

### T4. No Session Rename Mode / `--here` CLI Flag

- **Blocker**: `tmuxp load` (`cli/load.py`) has no `--here` flag. `WorkspaceBuilder.iter_create_windows()` always creates new windows via `session.new_window()` (line 649). Additionally, teamocil always renames the current session (`session.rb:18-20`), regardless of `--here`; the `--here` flag only affects **window** behavior (reuse current window for first window instead of creating new). tmuxp's `--append` flag partially covers session rename mode, but does not rename the session.
- **Blocks**: teamocil `--here` (reuse current window for first window) and teamocil session rename (always active, not conditional on `--here`).
- **Required**:
  1. Add `--here` flag to `cli/load.py` (around line 516, near `--append`).
  2. Pass `here=True` through to `WorkspaceBuilder.build()`.
  3. In `iter_create_windows()`, when `here=True` and first window: use `window.rename_window(name)` instead of `session.new_window()`, and send `cd <root>` via `pane.send_keys()` for directory change.
  4. Adjust `first_window_pass()` logic (line 864).
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
| `shell_command` (session-level) | tmuxinator importer | `importers.py:71` | Not a valid session key | **Bug** (I1 Bug B): `pre` commands lost when both `pre` and `pre_window` exist |
| `config` | tmuxinator importer | `importers.py:48,55` | Never read | Dead data — extracted `-f` path goes nowhere |
| `socket_name` | tmuxinator importer | `importers.py:63` | Never read | Dead data — CLI uses `-L` flag |
| `clear` | teamocil importer | `importers.py:158` | Never read | Dead data — builder doesn't read it, but libtmux has `Pane.clear()` (L4) |
| `height` (pane) | teamocil importer | passthrough (not popped) | Never read | Dead data — `width` is popped but `height` passes through silently |
| `target` (pane) | teamocil importer | passthrough (not popped) | Never read | Dead data — accidentally preserved via dict mutation, but libtmux has `Pane.split(target=...)` (L4) |
| `shell_command_after` | teamocil importer | `importers.py:166` | Never read | Dead data — tmuxp has no after-command support |

## Importer Bugs (No Builder Changes Needed)

### I1. tmuxinator `pre` / `pre_window` Mapping Bugs

Two bugs in `importers.py:70-81`, covering both code paths for the `pre` key:

#### Bug A: Solo `pre` maps to wrong key (NEW — 2026-03-06)

- **Bug**: When only `pre` exists (no `pre_window`) (`importers.py:77-81`), it maps to `shell_command_before` — a per-pane key that runs before each pane's commands. But tmuxinator's `pre` is a session-level hook that runs **once** before any windows are created. The correct target is `before_script`.
- **Effect**: Instead of running once at session start, the `pre` commands run N times (once per pane) as pane setup commands. This changes both the semantics (pre-session → per-pane) and the execution count.

#### Bug B: Combo `pre` + `pre_window` loses `pre` commands

- **Bug**: When both `pre` and `pre_window` exist (`importers.py:70-76`):
  1. `pre` maps to `shell_command` (line 71) — invalid session-level key, silently ignored by builder. The `pre` commands are lost entirely (see Dead Config Keys table).
  2. The `isinstance` check on line 73 tests `workspace_dict["pre"]` type to decide how to wrap `workspace_dict["pre_window"]` — it should check `pre_window`'s type, not `pre`'s. When `pre` is a string but `pre_window` is a list, `pre_window` gets double-wrapped as `[["cmd1", "cmd2"]]` (nested list). When `pre` is a list but `pre_window` is a string, `pre_window` won't be wrapped in a list — leaving a bare string where a list is expected.

#### Correct mapping

- `pre` → `before_script` (session-level, runs once before windows)
- `pre_window` → `shell_command_before` (per-pane, runs before each pane's commands)

#### `before_script` shell limitation

`before_script` is executed via `subprocess.Popen` after `shlex.split()` in `util.py:27-32` — **without `shell=True`**. This means shell constructs (pipes `|`, `&&`, redirects `>`, subshells `$(...)`) won't work in `before_script` values. For inline shell commands, the forward path is the `on_project_start` config key (T6), which would use `shell=True` or write a temp script.

### I2. tmuxinator `cli_args` / `tmux_options` Fragile Parsing

- **Bug**: `str.replace("-f", "").strip()` (`importers.py:50-60`) does a global string replacement, not flag-aware parsing. A value like `"-f ~/.tmux.conf -L mysocket"` would produce `"~/.tmux.conf -L mysocket"` as the `config` value (including the `-L` flag in a file path). Also ignores `-L` (socket name) and `-S` (socket path) flags entirely.
- **Fix**: Use proper argument parsing (e.g., `shlex.split()` + iterate to find `-f` flag and its value).

### I3. teamocil Redundant Filter Loops

- **Bug**: `for _b in w["filters"]["before"]:` loops (`importers.py:160-166`) iterate N times but set the same value each time.
- **Fix**: Replace with direct assignment.

### I4. teamocil v1.x Format Not Supported

- **Bug**: Importer assumes v0.x format. String panes cause incorrect behavior (`"cmd" in "git status"` checks substring, not dict key). `commands` key (v1.x) not mapped.
- **Fix**: Add format detection. Handle string panes, `commands` key, `focus`, and `options`.
- **Also**: v0.x pane `width` is silently dropped (`importers.py:178-180`) with a TODO but no user warning. `height` is not even popped — it passes through as a dead key. Since libtmux's `Pane.resize()` exists (L4), the importer could preserve both `width` and `height` and the builder could call `pane.resize(width=value)` or `pane.resize(height=value)` after split. Alternatively, warn the user.

### I5. tmuxinator Missing Keys

Not imported but translatable:
- `rvm` → `shell_command_before: ["rvm use {value}"]`
- `pre_tab` → `shell_command_before` (deprecated predecessor to `pre_window`)
- `startup_window` → find matching window, set `focus: true`
- `startup_pane` → find matching pane, set `focus: true`
- `on_project_first_start` → `before_script` (only if value is a single command or script path; multi-command strings joined by `;` won't work since `before_script` uses `Popen` without `shell=True`)
- `post` → deprecated predecessor to `on_project_exit`; runs after windows are built on every invocation. No tmuxp equivalent until T6 lifecycle hooks exist.
- `socket_path` → warn user to use CLI `-S` flag
- `attach: false` → warn user to use CLI `-d` flag

### I6. teamocil Missing Keys

Not imported but translatable:

**v1.x keys** (same key names in tmuxp):
- `commands` → `shell_command`
- `focus` (window) → `focus` (pass-through)
- `focus` (pane) → `focus` (pass-through)
- `options` (window) → `options` (pass-through)
- String pane shorthand → `shell_command: [command]`

**v0.x keys**:
- `with_env_var` → `environment: { TEAMOCIL: "1" }` (default `true` in v0.x; maps to session-level `environment` key)
- `height` (pane) → should be popped like `width` (currently passes through as dead key)

### I7. Importer TODOs Need Triage

`importers.py:132-134` lists `with_env_var` and `cmd_separator` as TODOs (with `clear` at line 133 in between). Both are verified v0.x features (present in teamocil's `0.4-stable` branch at `lib/teamocil/layout/window.rb`), not stale references:

- **`with_env_var`** (line 132): When `true` (the default in v0.x), exports `TEAMOCIL=1` in each pane. Should map to `environment: { TEAMOCIL: "1" }` (tmuxp's `environment` key works at session level via `Session.set_environment()`, L4). Implement, don't remove.
- **`clear`** (line 133): Already imported at line 158 but builder ignores it. libtmux has `Pane.clear()` (L4), so builder support is feasible.
- **`cmd_separator`** (line 134): Per-window string (default `"; "`) used to join commands before `send-keys`. Irrelevant for tmuxp since it sends commands individually. Remove TODO.

## Test Coverage Gaps

Current importer test fixtures cover ~40% of real-world config patterns. Key gaps by severity:

### Tier 1: Will Crash or Silently Lose Data

- **v1.x teamocil string panes**: `panes: ["git status"]` → `TypeError` (importer tries `"cmd" in p` on string)
- **v1.x teamocil `commands` key**: `commands: [...]` → silently dropped (only `cmd` recognized)
- **tmuxinator `rvm`**: Completely ignored by importer (only `rbenv` handled)
- **tmuxinator `pre` scope bug**: Tests pass because fixtures don't verify execution semantics

### Tier 2: Missing Coverage

- **YAML aliases/anchors**: Real tmuxinator configs use `&defaults` / `*defaults` — no test coverage
- **Numeric/emoji window names**: `222:`, `true:`, `🍩:` — YAML type coercion edge cases untested
- **Pane title syntax**: `pane_name: command` dict form — no fixtures
- **`startup_window`/`startup_pane`**: Not tested
- **`pre_tab`** (deprecated): Not tested
- **Window-level `root` with relative paths**: Not tested
- **`tmux_options` with non-`-f` flags**: Not tested (importer bug I2)

### Required New Fixtures

When implementing Phase 1 import fixes, each item needs corresponding test fixtures. See `tests/fixtures/import_tmuxinator/` and `tests/fixtures/import_teamocil/` for existing patterns.

**tmuxinator fixtures needed**: YAML aliases, emoji names, numeric names, `rvm`, `pre_tab`, `startup_window`/`startup_pane`, pane titles, `socket_path`, multi-flag `tmux_options`

**teamocil fixtures needed**: v1.x format (`commands`, string panes, window `focus`/`options`), pane `height`, `with_env_var`, mixed v0.x/v1.x detection

## Implementation Priority

### Phase 1: Import Fixes (No Builder/libtmux Changes)

These fix existing bugs and add missing translations without touching the builder:

1. **I3**: Fix redundant filter loops (teamocil)
2. **I4**: Add v1.x teamocil format support
3. **I6**: Import teamocil v1.x keys (`commands`, `focus`, `options`, string panes)
4. **I5**: Import missing tmuxinator keys (`rvm`, `pre_tab`, `startup_window`, `startup_pane`)
5. **I1**: Fix `pre`/`pre_window` mapping (tmuxinator)
6. **I2**: Fix `cli_args` parsing (tmuxinator)
7. **I7**: Triage importer TODOs (implement `with_env_var`, remove `cmd_separator`)

### Phase 2: Builder Additions (tmuxp Only)

These add new config key handling to the builder. Each also needs a corresponding importer update:

1. **T1**: `synchronize` config key — straightforward `set_option()` call
   - Then update tmuxinator importer to import `synchronize` key (pass-through, same name)
2. **T3**: `shell_command_after` config key — straightforward `send_keys()` loop
   - teamocil importer already produces this key (I3 fixes the loop); builder just needs to read it
3. **T2**: Pane title config keys — **now unblocked** (L1 resolved in libtmux v0.55.0)
   - Use `pane.set_title()` in builder. Session-level options via `session.set_option()`.
   - Update tmuxinator importer for named pane syntax
4. **T4**: `--here` CLI flag — moderate complexity, uses existing libtmux APIs

### ~~Phase 3: libtmux Additions~~ — **COMPLETE** (libtmux v0.55.0, issue #635 closed)

All libtmux API additions shipped in v0.55.0 (2026-03-07). tmuxp pins `libtmux~=0.55.0`.

- ~~**L1**: `Pane.set_title()`~~ → `pane.py:834-859`
- ~~**L2**: `Server(tmux_bin=...)`~~ → `server.py:142`
- ~~**L3**: Pre-execution `logger.debug`~~ → `common.py:263-268`

### Phase 4: New CLI Commands

1. **T5**: `tmuxp stop` command
2. **T10**: `tmuxp new`, `tmuxp copy`, `tmuxp delete` commands

### Phase 5: CLI Flags & Larger Features

1. **T7**: `--no-shell-command-before` flag — simple
2. **T9**: `--debug` / dry-run mode — **now unblocked** (L3 resolved in libtmux v0.55.0)
3. **T6**: Lifecycle hook config keys — complex, needs design
4. **T8**: Config templating — significant architectural addition
