# /implement — Plan and Implement from notes/plan.md

Orchestrates the full implementation workflow: plan → implement → verify → commit → document.

## Reference Codebases

- **tmuxinator**: `~/study/ruby/tmuxinator/`
- **teamocil**: `~/study/ruby/teamocil/`
- **tmux**: `~/study/c/tmux/`
- **libtmux**: `~/work/python/libtmux/`
- **tmuxp**: `~/work/python/tmuxp/`

## Workflow

### Phase 1: Planning Mode

1. **Read the plan**: Load `notes/plan.md` to understand what needs to be implemented
2. **Select a task**: Pick the highest priority incomplete item from the plan
3. **Research**:
   - Read relevant tmuxinator/teamocil Ruby source for behavior reference
   - Read libtmux Python source for available APIs
   - Read tmuxp source for integration points
4. **Create implementation plan**: Design the specific changes needed
5. **Exit planning mode** with the finalized approach

### Phase 2: Implementation

1. **Make changes**: Edit the necessary files
2. **Follow conventions**: Match existing code style, use type hints, add docstrings

### Phase 3: Verification

Run the full QA suite:

```bash
uv run ruff check . --fix --show-fixes
uv run ruff format .
uv run mypy
uv run py.test --reruns 0 -vvv
```

All checks must pass before proceeding.

### Phase 4: Commit Implementation

Commit the implementation changes with a descriptive message following the project's commit conventions (e.g., `feat:`, `fix:`, `refactor:`).

### Phase 5: Update Documentation

1. **Update `notes/completed.md`**: Add entry for what was implemented
   - Date
   - What was done
   - Files changed
   - Any notes or follow-ups

2. **Update `notes/plan.md`**: Mark the item as complete or remove it

3. **Commit notes separately**: Use message like `notes: Mark <feature> as complete`

## Output

After completion, report:
- What was implemented
- Files changed
- Test results summary
- What remains in the plan

## Notes

- If tests fail, fix the issues before committing
- If libtmux changes are needed, note them but don't modify libtmux in this workflow
- One logical change per run — don't implement multiple unrelated items
