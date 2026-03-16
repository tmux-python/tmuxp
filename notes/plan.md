# Parity Implementation Plan

*Last updated: 2026-03-15*
*Based on: parity-tmuxinator.md, parity-teamocil.md, import-tmuxinator.md, import-teamocil.md*

## libtmux Limitations

### L1. No `Pane.set_title()` Method — **RESOLVED in libtmux v0.55.0**

- **Status**: `Pane.set_title(title)` added at `pane.py:834-859`. Unblocks T2 (pane titles).
- ~~**Blocker**: libtmux has no method wrapping `select-pane -T <title>`.~~
- ~~**Blocks**: Pane titles (tmuxinator feature: named pane syntax `pane_name: command` → `select-pane -T`).~~
- ~~**Required**: Add `Pane.set_title(title: str)` method.~~

### L2. Hardcoded tmux Binary Path — **RESOLVED in libtmux v0.55.0**

- **Status**: `Server(tmux_bin=...)` added at `server.py:131-146`. Unblocks tmuxinator `tmux_command` support.
- ~~**Blocker**: `shutil.which("tmux")` is hardcoded in two independent code paths.~~
- ~~**Blocks**: Wemux support (tmuxinator `tmux_command: wemux`).~~
- ~~**Required**: Add optional `tmux_bin` parameter to `Server.__init__()`.~~

### L3. No Dry-Run / Command Preview Mode — **RESOLVED in libtmux v0.55.0**

- **Status**: Pre-execution `logger.debug` added at `common.py:263-268`. Unblocks T9 (dry-run mode).
- ~~**Blocker**: `tmux_cmd` always executes commands with no pre-execution logging.~~
- ~~**Blocks**: `--debug` / dry-run mode (both tmuxinator and teamocil have this).~~
- ~~**Required**: Add pre-execution logging at DEBUG level.~~
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

### T1. `synchronize` Config Key ✅ Resolved

Resolved in `feat(loader[expand])` — `expand()` desugars `synchronize: true/before/after` into `options`/`options_after` with `synchronize-panes: on`. The builder's existing `options` and `options_after` handling applies the setting. Tests: `test_synchronize` (builder integration), `test_expand_synchronize` (unit).

### T2. Pane Title Config Key ✅ Resolved

Resolved in `feat(loader[expand],builder[iter_create_panes])` — Session-level `enable_pane_titles`/`pane_title_position`/`pane_title_format` desugared in `expand()` into per-window `options` (`pane-border-status`, `pane-border-format`). Pane-level `title` handled in `iter_create_panes()` via `pane.set_title()`. Tests: `test_pane_titles` (builder integration), `test_expand_pane_titles`/`_disabled`/`_defaults` (unit).

### T3. `shell_command_after` Config Key ✅ Resolved

Resolved in `feat(builder[config_after_window],loader[expand])` — `expand()` normalizes `shell_command_after` via `expand_cmd()`, then `config_after_window()` sends each command to every pane in the window. Tests: `test_shell_command_after` (builder integration), `test_expand_shell_command_after` (unit).

### T4. No Session Rename Mode / `--here` CLI Flag ✅ Resolved

Resolved in `feat(cli[load],builder)` — `--here` flag added to CLI, passed through `load_workspace` → `_dispatch_build` → `build()` → `iter_create_windows()`. In `build()`, renames session to match config. In `iter_create_windows()`, reuses active window for first window (rename + cd) instead of `first_window_pass` trick. Skips session-exists prompt. Tests: `test_here_mode` (builder integration).

### ~~T5. No `stop` / `kill` CLI Command~~ ✅

Resolved in `feat(cli[stop])` — `tmuxp stop <session-name>` command added. Follows `freeze.py` pattern: optional session-name positional arg with current-session fallback via `util.get_session()`, `-L`/`-S` socket pass-through. Kills session via `session.kill()`. Uses `Colors` semantic hierarchy for output (green success + magenta session name). Lifecycle hooks (T6 `on_project_stop`) will layer on top.

### T6. Lifecycle Hook Config Keys ✅ Resolved

Resolved in `feat(util,builder,cli[load,stop],loader)` — 4 lifecycle hook config keys added: `on_project_start` (runs on every `tmuxp load`, before session creation), `on_project_restart` (runs when reattaching to existing session), `on_project_exit` (fires on detach via tmux `set-hook client-detached`), `on_project_stop` (runs before `session.kill()` in `tmuxp stop`, stored in session env). `run_hook_commands()` helper uses `shell=True` for full shell support. `on_project_first_start` skipped (covered by `before_script`). Hook values expanded via `expandshell()` in `loader.expand()`. Tests: `test_run_hook_commands*` (unit), `test_on_project_exit_sets_hook*` / `test_on_project_stop_sets_environment` / `test_on_project_stop_sets_start_directory_env` (builder integration), `test_load_on_project_start_runs_hook` / `test_load_on_project_restart_runs_hook` (CLI load), `test_stop_runs_on_project_stop_hook` / `test_stop_without_hook` (CLI stop), `test_expand_lifecycle_hooks_*` (loader expand).

### T7. No `--no-shell-command-before` CLI Flag ✅ Resolved

Resolved in `feat(cli[load])` — `--no-shell-command-before` flag added to `tmuxp load`. When set, strips `shell_command_before` from session, window, and pane levels after `expand()` but before `trickle()`. Equivalent to tmuxinator's `--no-pre-window`.

### T8. Config Templating ✅ Resolved

Resolved in `feat(loader,cli[load])` — `render_template()` in `loader.py` replaces `{{ variable }}` expressions in raw config content before YAML/JSON parsing. `--set KEY=VALUE` CLI flag (repeatable) passes template context through `load_workspace()` → `ConfigReader._from_file(template_context=...)`. Zero new dependencies (regex-based, no Jinja2). Unknown `{{ var }}` expressions left unchanged. Coexists with existing `$ENV_VAR` expansion (which runs after YAML parsing in `expand()`). Tests: `test_render_template` (9 parametrized unit tests), `test_load_workspace_template_context`/`_no_context` (CLI integration).

### T9. `--debug` CLI Flag ✅ Resolved

Resolved in `feat(cli[load])` — `--debug` flag added to `tmuxp load` that shows tmux commands as they execute. Uses a `_TmuxCommandDebugHandler` that attaches to libtmux's `libtmux.common` logger and intercepts structured `tmux_cmd` extra fields. Implies `--no-progress` (spinner disabled). Handler is properly cleaned up on all return paths. Not a true dry-run (tmux commands still execute — required for API-based building), but provides the debugging visibility that tmuxinator `debug` and teamocil `--debug` offer.

### T10. Missing Config Management Commands ✅ Resolved

Resolved in `feat(cli[new,copy,delete])` — Three config management commands added:
- `tmuxp new <name>` creates workspace from template + opens in `$EDITOR`
- `tmuxp copy <source> <dest>` duplicates workspace configs (supports names and paths)
- `tmuxp delete <name> [-y]` removes workspace configs with confirmation prompt
All commands follow existing CLI patterns (`edit.py`, `convert.py`), use `Colors` semantic hierarchy, and integrate with `find_workspace_file()`/`get_workspace_dir()`. Skipped `implode` (destructive nuke-all, low value).

## Dead Config Keys

Keys produced by importers but silently ignored by the builder:

| Key | Producer | Builder Handling | Status |
|---|---|---|---|
| ~~`config`~~ | ~~tmuxinator importer~~ | ~~Never read~~ | ✅ Resolved — `load_workspace()` reads as fallback for `-f` CLI flag |
| ~~`socket_name`~~ | ~~tmuxinator importer~~ | ~~Never read~~ | ✅ Resolved — `load_workspace()` reads as fallback for `-L` CLI flag |
| ~~`clear`~~ | ~~teamocil importer~~ | ~~Never read~~ | ✅ Resolved — `config_after_window()` sends `clear` to all panes when `clear: true` |
| ~~`shell_command` (session-level)~~ | ~~tmuxinator importer~~ | ~~Not a valid session key~~ | ✅ Resolved — I1: `pre` now maps to `before_script` |
| ~~`shell_command_after`~~ | ~~teamocil importer~~ | ✅ `config_after_window()` | ✅ Resolved — T3 |
| ~~`height` (pane)~~ | ~~teamocil importer~~ | ~~Dead data~~ | ✅ Resolved — warned + dropped |
| ~~`start_window`/`start_pane`~~ | ~~tmuxinator importer~~ | ~~Dead data~~ | ✅ Resolved — converted to `focus: true` in importer |

## Importer Fixes — All ✅ Resolved

### I1. tmuxinator `pre` / `pre_window` Mapping ✅ Resolved

Resolved — `pre` now correctly maps to `before_script` (session-level, runs once). `pre_window`/`pre_tab` maps to `shell_command_before`. Type check on `pre_window_val` is correct. Multi-command `pre` lists log an info message suggesting split. Tests: `test3` (combo), `test5` (`pre` + `pre_tab`), `test_logs_info_on_multi_command_pre_list`.

### I2. tmuxinator `cli_args` / `tmux_options` Parsing ✅ Resolved

Resolved — Uses `shlex.split()` with proper flag-aware iteration. Supports `-f`, `-L`, `-S` flags. Tests: `test3` (single flag), `test4` (multi-flag).

### I3. teamocil Redundant Filter Loops ✅ Resolved

Resolved — Direct assignment replaces redundant loops. Tests: existing `test2` (filters fixture).

### I4. teamocil v1.x Format ✅ Resolved

Resolved — Handles string panes, `None` panes, `commands` key (v1.x), `cmd` key (v0.x). `width`/`height` warned and dropped. Tests: `test5` (v1.x format), `test6` (focus/options/height).

### I5. tmuxinator Missing Keys ✅ Resolved

Resolved — `rvm` → `shell_command_before`, `pre_tab` → alias for `pre_window`, `startup_window` → `focus: true` on matching window, `startup_pane` → `focus: true` on matching pane. Tests: `test5` (rvm/pre_tab/startup), `test_startup_window_*`, `test_startup_pane_*`.

### I6. teamocil Missing Keys ✅ Resolved

Resolved — v1.x: `commands` → `shell_command`, string panes handled, window `focus`/`options` pass-through. v0.x: `with_env_var` and `cmd_separator` log warnings. Tests: `test5` (v1.x), `test6` (focus/options), `test_warns_on_with_env_var_and_cmd_separator`.

### I7. Importer TODOs ✅ Resolved

Resolved — `with_env_var` logs warning (unsupported), `cmd_separator` logs warning (irrelevant for tmuxp), `width`/`height` warn and drop. Tests: `test_warns_on_width_height_drop`, `test_warns_on_with_env_var_and_cmd_separator`.

## Remaining Test Coverage Gaps

### Tier 1: Covered ✅

All previously-identified Tier 1 gaps (v1.x string panes, `commands` key, `rvm`, `pre` scope) are now fixed and tested.

### Tier 2: Edge Cases ✅ Resolved

- ~~**YAML aliases/anchors**~~: ✅ Tested — aliases resolve transparently via YAML parser before import
- ~~**Numeric/emoji window names**~~: ✅ Fixed + tested — `str(k)` coercion in importer prevents `TypeError` in `expandshell()`
- ~~**Pane title syntax**~~: ✅ Fixed + tested — `_convert_named_panes()` converts `{name: commands}` to `{shell_command, title}`

## Implementation Priority

### ~~Phase 1: Import Fixes~~ — **COMPLETE**

All importer bugs (I1-I7) resolved. Importers handle v1.x format, missing keys, proper `pre`/`pre_window` mapping, flag-aware `cli_args` parsing, `startup_window`/`startup_pane` → `focus: true`, and unsupported key warnings.

### ~~Phase 2: Builder Additions~~ — **COMPLETE**

All builder config keys resolved: T1 (`synchronize`), T2 (pane titles), T3 (`shell_command_after`), T4 (`--here`).

### ~~Phase 3: libtmux Additions~~ — **COMPLETE** (libtmux v0.55.0)

All libtmux API additions shipped in v0.55.0.

### ~~Phase 4: New CLI Commands~~ — **COMPLETE**

T5 (`tmuxp stop`), T10 (`tmuxp new`, `tmuxp copy`, `tmuxp delete`).

### ~~Phase 5: CLI Flags & Features~~ — **MOSTLY COMPLETE**

- ~~T7: `--no-shell-command-before` flag~~ ✅
- ~~T9: `--debug` mode~~ ✅
- ~~T6: Lifecycle hook config keys~~ ✅

### Phase 6: Remaining

1. ~~**T8**~~: ✅ Resolved — `{{ variable }}` templating with `--set KEY=VALUE` CLI flag.
2. ~~**Dead config keys**~~: ✅ Resolved — `config`, `socket_name`, `socket_path` now read as fallbacks in `load_workspace()`. CLI flags override.
3. ~~**`clear` config key**~~: ✅ Resolved — `config_after_window()` sends `clear` to all panes when `clear: true`.
4. ~~**Edge case test coverage**~~: ✅ Resolved — YAML aliases tested, numeric/emoji window names fixed + tested, pane title syntax fixed + tested.
