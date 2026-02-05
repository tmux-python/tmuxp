# Completed Work

Tracking completed items from the feature parity plan.

## Format

```
## YYYY-MM-DD: Brief description

**What**: What was implemented
**Files**: List of changed files
**Notes**: Any follow-up items or observations
```

---

<!-- Entries below -->

## 2026-02-04: Fix dead config keys (Phase 1 partial)

**What**: Read `socket_name`, `socket_path`, and `config` from workspace config in `load_workspace()`, with CLI args taking precedence.

**Files**:
- `src/tmuxp/cli/load.py` - Merge config values with CLI args before creating Server
- `tests/cli/test_load.py` - Add 5 parametrized test cases for config key precedence

**Notes**:
- This enables configs imported from tmuxinator (which set `socket_name` and `config` keys) to work correctly
- Remaining dead config keys from Phase 1: `shell_command_after`, `shell_command` (session-level), `clear`

## 2026-02-04: Support attach config key

**What**: Read `attach` key from workspace config to control detached mode. When `attach: false` is set, session loads in detached mode. CLI `-d` flag takes precedence.

**Files**:
- `src/tmuxp/cli/load.py` - Handle attach config key with CLI precedence
- `tests/cli/test_load.py` - Add 5 parametrized test cases for attach config

**Notes**:
- Enables tmuxinator-style `attach: false` configs to work correctly
- Remaining dead config keys: `shell_command` (session-level), `clear`

## 2026-02-04: Support shell_command_after in workspace configs

**What**: Add `shell_command_after` handling to `expand()` and `trickle()` functions. Commands are appended after pane commands in reverse order (pane → window → session), mirroring teardown semantics.

**Files**:
- `src/tmuxp/workspace/loader.py` - Handle shell_command_after in expand() and trickle()
- `tests/workspace/test_config.py` - Add 5 parametrized test cases

**Notes**:
- Enables teamocil's `filters.after` to work correctly when imported
- Remaining dead config keys: `clear`

## 2026-02-04: Support session-level shell_command

**What**: Read session-level `shell_command` in `trickle()` and prepend to all pane commands. This handles the tmuxinator import case where both `pre` and `pre_window` are present.

**Files**:
- `src/tmuxp/workspace/loader.py` - Handle session-level shell_command in trickle(), fix expand_cmd() type hint
- `tests/workspace/test_config.py` - Add 4 parametrized test cases

**Notes**:
- Session-level shell_command runs before shell_command_before

## 2026-02-04: Support window-level clear option

**What**: Handle teamocil's `clear` window option by inserting a `clear` command before pane commands when `clear: true` is set at window level.

**Files**:
- `src/tmuxp/workspace/loader.py` - Handle clear option in trickle()
- `tests/workspace/test_config.py` - Add 4 parametrized test cases

**Notes**:
- This completes Phase 1 (all dead config keys now handled)
- Clear runs after shell_command_before but before pane commands

## 2026-02-04: Support synchronize config key as sugar

**What**: Add tmuxinator-compatible `synchronize` key that expands to `options` or `options_after` with `synchronize-panes: on`.

**Files**:
- `src/tmuxp/workspace/loader.py` - Expand synchronize to options/options_after
- `tests/workspace/test_config.py` - Add 5 parametrized test cases

**Notes**:
- `synchronize: true` or `"before"` -> `options: {synchronize-panes: on}`
- `synchronize: "after"` -> `options_after: {synchronize-panes: on}`
- This completes Phase 2 (all missing config keys now supported)

## 2026-02-04: Fix tmuxinator importer pre_window and add rvm support

**What**: Fix tmuxinator importer to handle `pre_window` alone (without `pre`), add support for `pre_tab` (deprecated alias), and add `rvm` version manager support.

**Files**:
- `src/tmuxp/workspace/importers.py` - Fix pre_window handling, add pre_tab and rvm
- `tests/workspace/test_import_tmuxinator.py` - Add 9 parametrized test cases

**Notes**:
- `pre_window` alone now correctly maps to `shell_command_before`
- `pre_tab` is supported as deprecated alias for `pre_window`
- `rvm` support added alongside existing `rbenv` support

## 2026-02-04: Add synchronize and startup_window/pane to tmuxinator importer

**What**: Map tmuxinator's `synchronize`, `startup_window`, and `startup_pane` options to tmuxp equivalents.

**Files**:
- `src/tmuxp/workspace/importers.py` - Add synchronize and startup handling
- `tests/workspace/test_import_tmuxinator.py` - Add 8 parametrized test cases

**Notes**:
- `synchronize: true` or `"before"` -> `options: {synchronize-panes: on}`
- `synchronize: "after"` -> `options_after: {synchronize-panes: on}`
- `startup_window` -> `focus: true` on matching window
- `startup_pane` -> `focus: true` on matching pane (supports combined with startup_window)

## 2026-02-04: Fix tmuxinator importer loop bug and add post warning

**What**: Fix loop variable reassignment bug and add warning for unsupported `post` key.

**Files**:
- `src/tmuxp/workspace/importers.py` - Fix loop bug, add logging, warn on post
- `tests/workspace/test_import_tmuxinator.py` - Add test for post warning

**Notes**:
- Renamed `window_dict` to `new_window` in loop to avoid shadowing
- Added warning when `post` key is encountered (no tmuxp equivalent)

## 2026-02-04: Fix teamocil v1.4.2+ compatibility

**What**: Support modern teamocil format with string panes, `commands` key, and window/pane focus.

**Files**:
- `src/tmuxp/workspace/importers.py` - Comprehensive teamocil importer rewrite
- `tests/workspace/test_import_teamocil.py` - Add 6 parametrized test cases

**Notes**:
- String panes now converted to `{shell_command: "cmd"}`
- `commands` (v1.4.2) supported alongside `cmd`
- Window-level `options` and `focus` now supported
- Pane-level `focus` and `root` now supported
- Optional window names fall back to `window-N` index
- `target` key passed through from panes

## 2026-02-05: Add --no-shell-command-before CLI flag (Phase 4)

**What**: Add `--no-shell-command-before` flag to skip pre-window commands during workspace loading.

**Files**:
- `src/tmuxp/cli/load.py` - Add CLI arg, update CLILoadNamespace, update load_workspace() signature
- `src/tmuxp/workspace/loader.py` - Add skip_shell_command_before parameter to trickle()
- `tests/cli/test_load.py` - Add 2 tests for new flag
- `tests/workspace/test_config.py` - Add 5 parametrized test cases for trickle() with flag

**Notes**:
- Equivalent to tmuxinator's `--no-pre-window` flag
- Useful for quick session reload, debugging, and bypassing slow setup commands

## 2026-02-05: Add libtmux features for tmuxinator parity (Phase 5)

**What**: Added two libtmux features needed for full tmuxinator parity:
1. `Pane.set_title()` method for setting pane titles
2. `tmux_bin` parameter on Server for custom tmux binary path

**Branch**: `tmuxinator-parity` in libtmux repository

**Files** (libtmux):
- `src/libtmux/pane.py` - Add Pane.set_title() method using `select-pane -T`
- `src/libtmux/common.py` - Add tmux_bin kwarg to tmux_cmd.__init__()
- `src/libtmux/server.py` - Add tmux_bin parameter to Server.__init__(), update cmd() and raise_if_dead()
- `tests/test_pane.py` - Add 3 tests for set_title()
- `tests/test_server.py` - Add 3 tests for tmux_bin parameter
- `tests/test_common.py` - Add 2 tests for tmux_cmd with tmux_bin

**Notes**:
- `Pane.set_title()` enables tmuxinator's named panes feature
- `tmux_bin` enables tmuxinator's `tmux_command` config for wemux/byobu
- Requires libtmux release before tmuxp can use these features
- CHANGES updated with feature documentation
