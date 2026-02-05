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
- Remaining dead config keys: `shell_command_after`, `shell_command` (session-level), `clear`
