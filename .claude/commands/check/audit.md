---
description: Idempotent parity audit — checks deliverables, tmuxinator/teamocil parity, DX, pytest conventions, and test coverage
---

# /check:audit — Parity Audit

Idempotent status check for tmuxinator/teamocil parity work (issue #1016). Launches sub-agents to assess 6 dimensions, then synthesizes a status report with prioritized TODOs.

## Workflow

### Batch 1: Launch 3 Explore agents in parallel

#### Agent 1: Deliverable Check

Read these files and check each item:

- `src/tmuxp/workspace/importers.py`
- `src/tmuxp/workspace/builder.py` (search for `shell_command_after`, `synchronize`)
- `src/tmuxp/cli/load.py` (search for `--here`, `here`)
- `src/tmuxp/cli/__init__.py` (search for `stop`, `new`, `copy`, `delete`)

**Checklist** (mark ✅ done, ❌ missing, 🔧 partially done):

| ID | Item | What to check |
|----|------|---------------|
| I1 | `pre`/`pre_window` mapping | `pre` → `on_project_start` (not `before_script`/`shell_command_before`). `pre_window` → `shell_command_before` |
| I2 | `cli_args`/`tmux_options` parsing | Uses `shlex.split()` token iteration, not `.replace("-f", "")` |
| I3 | Filter loop fix | Direct assignment with truthiness guard, not `for _b in` loop |
| I4 | v1.x teamocil format | String panes and `commands` key handled |
| I5 | Missing tmuxinator keys | `rvm`, `pre_tab`, `startup_window`, `startup_pane` handled |
| I6 | Missing teamocil keys | `focus`, `target`, `options` explicitly copied (not accidental mutation) |
| I7 | Importer TODOs | `with_env_var` → window `environment`, stale TODO docstring removed |
| T1 | `synchronize` desugar | Desugared to `options`/`options_after` in importer |
| T3 | `shell_command_after` | Processed in `config_after_window()` in builder |
| T4 | `--here` CLI flag | Flag exists in load.py, mutually exclusive with `--append` |
| T5 | `tmuxp stop` | Command registered in CLI |
| T10 | `tmuxp new/copy/delete` | Commands registered in CLI |

#### Agent 2: Tmuxinator Parity

Read `src/tmuxp/workspace/importers.py` (function `import_tmuxinator`).

If available, also read tmuxinator Ruby source at `~/study/ruby/tmuxinator/lib/tmuxinator/project.rb`.

For each tmuxinator config key, check if it's handled in the importer and if a test fixture covers it:

| Key | Handled? | Mapping correct? | Test fixture? |
|-----|----------|-------------------|---------------|
| `name` | | | |
| `project_name` | | | |
| `root` / `project_root` | | | |
| `pre` (string) | | | |
| `pre` (list) | | | |
| `pre_window` | | | |
| `pre_tab` | | | |
| `rbenv` | | | |
| `rvm` | | | |
| `tmux_options` / `cli_args` | | | |
| `socket_name` | | | |
| `startup_window` | | | |
| `startup_pane` | | | |
| `synchronize` (true/before/after/false) | | | |
| `tabs` (alias for windows) | | | |
| `on_project_start/exit/stop` | | | |
| `enable_pane_titles` | | | |
| `pane_title_position/format` | | | |
| window `pre` | | | |
| window `root` | | | |
| window `layout` | | | |
| window `panes` (list of strings) | | | |
| window `panes` (list of dicts) | | | |

#### Agent 3: Teamocil Parity

Read `src/tmuxp/workspace/importers.py` (function `import_teamocil`).

If available, also read teamocil Ruby source at `~/study/ruby/teamocil/lib/teamocil/tmux/`.

For each teamocil config key, check if it's handled in the importer and if a test fixture covers it:

| Key | Handled? | v0.x? | v1.x? | Test fixture? |
|-----|----------|-------|-------|---------------|
| `session.name` | | | | |
| `session.root` | | | | |
| `windows[].name` | | | | |
| `windows[].root` | | | | |
| `windows[].layout` | | | | |
| `windows[].clear` | | | | |
| `windows[].filters.before` | | | | |
| `windows[].filters.after` | | | | |
| `windows[].with_env_var` | | | | |
| `windows[].cmd_separator` | | | | |
| `windows[].focus` | | | | |
| `windows[].options` | | | | |
| `splits` (alias for panes) | | | | |
| `panes[].cmd` (string) | | | | |
| `panes[].cmd` (list) | | | | |
| `panes[].commands` (v1.x) | | | | |
| `panes[]` as string (v1.x) | | | | |
| `panes[]` as None | | | | |
| `panes[].focus` | | | | |
| `panes[].target` | | | | |
| `panes[].width` | | | | |
| `panes[].height` | | | | |

### Batch 2: Launch 3 more Explore agents in parallel

#### Agent 4: DX Happiness

Read:
- `src/tmuxp/cli/load.py` — flags, help strings, error messages
- `src/tmuxp/cli/import_config.py` — import flow warnings
- `src/tmuxp/util.py` — `run_before_script()` behavior

Check:
- Import CLI warns about manual adjustments after import
- Unsupported keys (width, height) produce log warnings (not silent drops)
- Multi-command `pre` lists warn with actionable guidance
- `--here` outside tmux gives clear error (not cryptic traceback)
- Schema validation catches bad imports before tmux session creation
- `tmuxp stop` has `--yes` flag for scripting

Report each issue with severity: **blocker** / **warning** / **nice-to-have**.

#### Agent 5: Pytest Happiness

Read all test files in:
- `tests/workspace/test_import_tmuxinator.py`
- `tests/workspace/test_import_teamocil.py`
- `tests/workspace/test_builder.py`
- `tests/cli/test_load.py` (if exists)

And all fixture files in:
- `tests/fixtures/import_tmuxinator/*.py`
- `tests/fixtures/import_teamocil/*.py`

**Convention checklist** (from CLAUDE.md):

| Convention | Status | Evidence |
|------------|--------|----------|
| Functional tests only (no `class TestFoo:`) | | |
| `NamedTuple` fixture classes with `test_id` | | |
| `@pytest.mark.parametrize` with `ids=` | | |
| Fixture modules export `*_yaml`, `*_dict`, `expected` | | |
| Tests call `validation.validate_schema()` | | |
| No `unittest.mock` (use `monkeypatch`) | | |
| No `tempfile` (use `tmp_path`) | | |
| `from __future__ import annotations` | | |
| `import typing as t` namespace | | |

List any violations with file path and line number.

#### Agent 6: Test Coverage

Read `src/tmuxp/workspace/importers.py` and enumerate every branch/condition.
Read all test files and fixtures to determine which branches are covered.

**`import_tmuxinator()` branches**:

| Branch | Condition | Tested? | Test ID |
|--------|-----------|---------|---------|
| session name | `project_name` present | | |
| session name | `name` present | | |
| session name | neither → `None` | | |
| start dir | `project_root` present | | |
| start dir | `root` present | | |
| cli args | `cli_args` with `-f` | | |
| cli args | `tmux_options` with `-f` | | |
| cli args | multi-flag (`-f -L`) | | |
| socket | `socket_name` present | | |
| pre | `pre` string only | | |
| pre | `pre` list single cmd | | |
| pre | `pre` list multi cmd (warning) | | |
| pre | `pre` + `pre_window` combo | | |
| pre_window | string | | |
| pre_window | list | | |
| pre_tab | alias for pre_window | | |
| rbenv | present | | |
| rvm | present | | |
| tabs | alias for windows | | |
| synchronize | true / "before" | | |
| synchronize | "after" | | |
| synchronize | false | | |
| startup_window | present | | |
| startup_pane | present | | |
| window | string value | | |
| window | None value | | |
| window | list value | | |
| window | dict with pre/panes/root/layout | | |

**`import_teamocil()` branches**:

| Branch | Condition | Tested? | Test ID |
|--------|-----------|---------|---------|
| session wrapper | `session` key present | | |
| session name | `name` present / absent | | |
| session root | `root` present | | |
| window clear | `clear` present | | |
| filters before | non-empty list | | |
| filters before | empty list | | |
| filters after | non-empty list | | |
| filters after | empty list | | |
| with_env_var | true | | |
| with_env_var | false | | |
| window root | present | | |
| splits alias | `splits` → `panes` | | |
| pane cmd | string | | |
| pane cmd | list | | |
| pane commands | v1.x key | | |
| pane string | v1.x format | | |
| pane None | blank pane | | |
| pane focus | present | | |
| pane target | present | | |
| pane width | warning | | |
| pane height | warning | | |
| window layout | present | | |
| window focus | present | | |
| window options | present | | |

### Synthesis

After all 6 agents complete, synthesize results into:

**Status Summary** — one line per dimension:
```
1. Deliverables:  X/12 items complete
2. Tmuxinator:    X/Y keys handled, X tested
3. Teamocil:      X/Y keys handled, X tested
4. DX:            X blockers, Y warnings
5. Pytest:        X/Y conventions met
6. Coverage:      X/Y branches tested
```

**Prioritized TODO** — ordered by impact:
1. Blockers (broken behavior, data loss)
2. Missing features (unhandled keys)
3. Test gaps (untested branches)
4. Convention violations
5. Nice-to-have DX improvements

**Ready to ship?** — Yes / No, with blocking items listed.
