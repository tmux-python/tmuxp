# Parity Implementation Plan

*Last updated: 2026-03-15*

## libtmux Limitations

### L1. No `Pane.set_title()` Method — **RESOLVED in libtmux v0.55.0**

**Status**: `Pane.set_title(title)` added at `pane.py:834-859`. Unblocks T2.

### L2. Hardcoded tmux Binary Path — **RESOLVED in libtmux v0.55.0**

**Status**: `Server(tmux_bin=...)` added at `server.py:142`. Unblocks tmuxinator `tmux_command`.

### L3. No Dry-Run / Command Preview Mode — **RESOLVED in libtmux v0.55.0**

**Status**: Pre-execution `logger.debug` added at `common.py:263-268`. Unblocks T9.

**Note**: Since tmuxp uses libtmux API calls (not command strings), a true dry-run would require a recording layer in `WorkspaceBuilder` that logs each API call. This is architecturally different from tmuxinator/teamocil's approach and may not be worth full parity.

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

> **Status (2026-05-09):** Every gap below has shipped on the
> `tmuxinator-parity` branch. tmuxp now has feature parity with
> tmuxinator and teamocil. Sections below remain as historical design
> references; see `CHANGES` for the user-visible feature summary.

### T1. No `synchronize` Config Key

- **Blocker**: `WorkspaceBuilder` (`builder.py`) does not check for a `synchronize` key on window configs. Silently ignored if present.
- **Blocks**: Pane synchronization (tmuxinator `synchronize: true/before/after`). tmuxinator deprecates `true`/`before` in favor of `after` (`project.rb:21-29`), but all three values still function — import should honor original semantics.
- **Required**: For `before`/`true`, call `window.set_option("synchronize-panes", "on")` in `build()` ~line 541 (after `on_window_create` plugin hook, before `iter_create_panes()` loop). For `after`, same call in `config_after_window()` ~line 822. For `false`/omitted, no action.
- **Note**: In tmux 3.2+ (tmuxp's minimum), `synchronize-panes` is a dual-scope option (window\|pane, `options-table.c:1423`); window-level set propagates to later splits.
- **Non-breaking**: New optional config key.

### Simple gaps (table form)

| ID | Gap | Required change | Notes |
|---|---|---|---|
| T3 | No `shell_command_after` config key | In `config_after_window()` ~line 822 (or after `iter_create_panes()`), read `window_config.get("shell_command_after", [])` and `pane.send_keys()` to each pane | teamocil importer already produces this on the **window** dict (`importers.py:149`); only builder read is missing |
| T7 | No `--no-shell-command-before` CLI flag | Add flag to `cli/load.py`; clear `shell_command_before` from all levels before `trickle()` (`loader.py:245-256`) | Mirrors tmuxinator `--no-pre-window` |
| T10 | Missing config management commands (`new`, `copy`, `delete`) | Add CLI commands in `cli/`; straightforward file operations | Mirrors tmuxinator `new`, `copy`, `delete`, `implode` |

### T2. No Pane Title Config Key

- **Blocker**: `WorkspaceBuilder` has no handling for pane `title` key or session-level `enable_pane_titles` / `pane_title_position` / `pane_title_format`.
- **Blocks**: Pane titles (tmuxinator named pane syntax).
- **Required**:
  1. Session-level: set `pane-border-status` and `pane-border-format` options via `session.set_option()` in `build()` alongside other session options (lines 529-539).
  2. Pane-level: call `pane.cmd("select-pane", "-T", title)` after commands are sent in `iter_create_panes()`, before focus handling (around line 816). Requires L1 (libtmux `set_title()`), or can use `pane.cmd()` directly.
- **Config keys**: `enable_pane_titles: true`, `pane_title_position: top`, `pane_title_format: "..."` (session-level). `title: "my-title"` (pane-level).
- **Non-breaking**: New optional config keys.

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

For full bug analysis with file:line refs, see `notes/import-tmuxinator.md` and `notes/import-teamocil.md`.

| ID | Importer | Bug | Fix scope |
|---|---|---|---|
| I1 | tmuxinator | `pre` (alone) maps to `shell_command_before` (per-pane) instead of `before_script` (once); combo `pre` + `pre_window` writes `pre` to invalid `shell_command` key and `isinstance` checks the wrong var (lines 70-81) | **Resolved**: maps `pre` → `before_script`; warns on shell metacharacters (Popen runs without `shell=True`). Long-term shell fix waits on T6. |
| I2 | tmuxinator | `cli_args`/`tmux_options` use `str.replace("-f", "")` (lines 50-60); breaks on `-L`/`-S` flags or paths containing `-f` | **Resolved**: shlex-based parsing extracts `-f`/`-L`/`-S`; warns on unknown flags. |
| I3 | teamocil | Redundant `for _b in w["filters"]["before"]` loops set same value N times (lines 160-166) | **Resolved**: direct assignment. |
| I4 | teamocil | v1.x format not detected: string panes cause `"cmd" in str` substring check; `commands` key dropped; pane `width` silently dropped, `height` passes through | **Resolved**: dispatch to `_import_teamocil_v0x` / `_import_teamocil_v1x`; v0.x detected by `session:` wrapper OR window `splits`/`filters`/pane `cmd`. v1.x handles string panes, `commands`, per-window/pane `focus`, window `options`. |
| I5 | tmuxinator | Missing translations: `rvm`, `pre_tab`, `startup_window`, `startup_pane`, `on_project_first_start`, `post`, `socket_path`, `attach: false` | **Resolved**: rbenv → rvm → pre_tab → pre_window OR-fallback chain implemented; `startup_window`/`startup_pane` resolved by name or int → `focus: true`; `on_project_first_start` → `before_script`; `socket_path` pass-through; `attach: false` warns. `post` deferred (needs T6). |
| I6 | teamocil | Missing v1.x mappings (`commands`, window/pane `focus`, window `options`, string pane shorthand) and v0.x `with_env_var`/`height` | **Resolved** by I4 (v1.x mappings) + I7 (`with_env_var`); v0.x `height`/`target` now popped with WARNING. |
| I7 | teamocil | TODOs at `importers.py:132-134` (`with_env_var`, `clear`, `cmd_separator`) — first two are real v0.x features, third is irrelevant | **Resolved**: `with_env_var` → session-level `environment: {TEAMOCIL: "1"}` for v0.x configs; `cmd_separator` warns; `clear` preserved with WARNING (builder support deferred). |

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
