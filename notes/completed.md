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
