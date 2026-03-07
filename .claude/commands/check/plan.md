---
description: Audit parity status and generate a commit-by-commit implementation plan with QA gates
---

# /check:plan — Parity Implementation Plan

Runs the same audit as `/check:audit`, then converts findings into an ordered sequence of atomic commits. Each commit has a mandatory QA gate. Source and test commits are separate.

## Phase 1: Audit

Run `/check:audit` inline — launch 6 Explore agents in 2 batches of 3 (see `.claude/commands/check/audit.md` for the full agent definitions). Collect results for all 6 dimensions:

1. Deliverable Check
2. Tmuxinator Parity
3. Teamocil Parity
4. DX Happiness
5. Pytest Happiness
6. Test Coverage

## Phase 2: Generate Commit Plan

Using audit results, generate a **numbered commit sequence**. Group by logical topic, ordered by priority:

1. **Bug fixes first** (broken behavior, data loss)
2. **Missing features** (unhandled keys, new code paths)
3. **Test coverage** (new fixtures and test cases)
4. **DX improvements** (warnings, validation, error messages)
5. **Future features** (CLI commands, lifecycle hooks)

### Commit Structure Rules

Each commit entry must specify:

```
### Commit N: <commit message>

**Files**: list of files to modify
**Changes**:
- Specific change 1
- Specific change 2
**Test fixtures** (if test commit): list of new fixture files/test IDs
**Depends on**: Commit X (if sequential dependency)
```

### Commit Pairing Convention

Source and tests are **separate commits** (per AGENTS.md):

- Source commit: `fix(importers[import_tmuxinator]): Fix pre mapping to before_script`
- Test commit: `test(importers[import_tmuxinator]): Add pre mapping fixtures`

### Commit Message Format

Follow project conventions:
```
Scope(type[detail]): concise description

why: Explanation of necessity or impact.
what:
- Specific technical changes made
```

## Phase 3: QA Gate

**Before every commit**, run the full QA suite:

```bash
uv run ruff check . --fix --show-fixes && uv run ruff format . && uv run mypy && uv run py.test -vvv
```

**All four commands must pass.** If `ruff check --fix` modifies files, stage those fixes into the same commit. If `mypy` or `py.test` fails, fix the issue before committing.

Do NOT use `--no-verify` or skip any step.

## Phase 4: Execute

For each commit in the plan:

1. **Make the changes** described in the commit entry
2. **Run the QA gate** — all 4 commands must pass
3. **Stage specific files** — `git add <files>`, never `git add .` or `git add -A`
4. **Commit** with the specified message (use heredoc for multi-line)
5. **Verify** — `git log --oneline -1` to confirm
6. **Proceed** to next commit

If a commit fails QA:
- Fix the issue
- Re-run QA
- Create a **new** commit (never amend)

## Phase 5: Re-audit

After all commits are done, re-run the audit (Phase 1) to verify progress. Report:

```
Before: X/Y items complete
After:  X/Y items complete
Remaining: list of items still TODO
```

## Reference

- **Audit dimensions**: `.claude/commands/check/audit.md`
- **Implementation patterns**: `.claude/commands/implement.md`
- **Commit conventions**: `CLAUDE.md` (Git Commit Standards)
- **Test patterns**: `CLAUDE.md` (Testing Guidelines)
- **Primary source**: `src/tmuxp/workspace/importers.py`
- **Test files**: `tests/workspace/test_import_tmuxinator.py`, `tests/workspace/test_import_teamocil.py`
- **Fixture dirs**: `tests/fixtures/import_tmuxinator/`, `tests/fixtures/import_teamocil/`
