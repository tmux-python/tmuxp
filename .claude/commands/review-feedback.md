---
description: Process external code review feedback — validate each point, apply valid fixes as separate commits
argument-hint: "Paste the external code review feedback here"
allowed-tools: Bash(git diff:*), Bash(git log:*), Bash(git branch:*), Bash(git status:*), Bash(git add:*), Bash(git commit:*), Bash(uv run ruff:*), Bash(uv run mypy:*), Bash(uv run py.test:*), Bash(uv run pytest:*), Read, Grep, Glob, Edit, Write
---

# External Code Review Feedback Processor

Process external code review feedback against the current branch. Validate each feedback point independently, apply valid fixes as separate atomic commits, and ensure all quality gates pass after each commit.

Review feedback to process: $ARGUMENTS

---

## Phase 1: Gather Context

**Goal**: Understand what changed on this branch and parse the review feedback.

**Actions**:

1. **Get the diff** against the trunk branch:
   ```
   git diff origin/master --stat
   git diff origin/master
   ```

2. **Get commit history** for this branch:
   ```
   git log origin/master..HEAD --oneline
   ```

3. **Read modified files** identified in the diff to understand the full context of each change

4. **Parse the review feedback** into a numbered list of discrete, actionable points. Each point should capture:
   - **What**: The specific issue or suggestion
   - **Where**: File and approximate location
   - **Category**: bug, style, logic, naming, performance, test gap, documentation, etc.

5. **Create a todo list** tracking each feedback point with its validation status

---

## Phase 2: Validate Each Feedback Point

**Goal**: Independently assess whether each feedback point is valid and actionable.

For EACH feedback point:

1. **Read the relevant code** — the exact lines the reviewer is referring to

2. **Assess validity** using these criteria:
   - **Valid**: The feedback identifies a real issue or improvement that aligns with project conventions (CLAUDE.md)
   - **Already addressed**: The issue was already fixed in a later commit on the branch
   - **Incorrect**: The reviewer misread the code or the suggestion would introduce a bug
   - **Out of scope**: Valid concern but belongs in a separate PR/issue
   - **Subjective/style**: Preference-based with no clear project convention favoring it

3. **Document the verdict** for each point:
   - If valid: note exactly what change is needed and in which file(s)
   - If invalid: note the specific reason (cite code, tests, or CLAUDE.md conventions)

4. **Present the validation results** to the user before making any changes:
   - List each feedback point with its verdict (valid / invalid / out of scope)
   - For invalid points, explain why concisely
   - For valid points, describe the planned fix
   - **Wait for user confirmation** before proceeding to Phase 3

---

## Phase 3: Apply Valid Fixes (One Commit Per Point)

**Goal**: Apply each valid feedback point as a separate, atomic commit.

**CRITICAL**: Process one feedback point at a time. Complete the full cycle for each before moving to the next.

For EACH valid feedback point:

### Step 1: Apply the Fix

- Make the minimal change that addresses the feedback
- Do not bundle unrelated changes
- Follow project conventions from CLAUDE.md:
  - `from __future__ import annotations` at top of files
  - `import typing as t` namespace style
  - NumPy docstring style
  - Functional tests only (no test classes)

### Step 2: Run Quality Gates

Run ALL quality gates and ensure they pass:

```bash
uv run ruff check . --fix --show-fixes
uv run ruff format .
uv run mypy
uv run py.test --reruns 0 -vvv
```

- If any gate fails, fix the issue before proceeding
- If a test fails due to the change, either:
  - Adjust the fix to be correct, OR
  - Update the test if the reviewer's feedback changes expected behavior
- ALL FOUR gates must pass before committing

### Step 3: Commit

Stage only the files changed for this specific feedback point:

```bash
git add <specific-files>
```

Use the project commit message format with HEREDOC:

```bash
git commit -m "$(cat <<'EOF'
Component(fix[subcomponent]) Brief description of the review feedback fix

why: Address code review feedback — <what the reviewer pointed out>
what:
- <specific change 1>
- <specific change 2>
EOF
)"
```

**Commit type guidance**:
- `fix` for bug fixes or correctness issues
- `refactor` for code clarity or structure improvements
- `style` for naming or formatting changes
- `docs` for documentation or docstring fixes
- `test` for test improvements

### Step 4: Verify Clean State

After committing, confirm:
```bash
git status
git diff
```

No uncommitted changes should remain before moving to the next feedback point.

---

## Phase 4: Summary

After processing all valid points, present a summary:

1. **Applied fixes**: List each committed fix with its commit hash
2. **Skipped points**: List each invalid/out-of-scope point with the reason
3. **Final verification**: Run the full quality gate one last time:
   ```bash
   uv run ruff check . --fix --show-fixes
   uv run ruff format .
   uv run mypy
   uv run py.test --reruns 0 -vvv
   ```
4. Report the final pass/fail status

---

## Recovery: Quality Gate Failure

If quality gates fail after applying a fix:

1. **Identify** which gate failed and why
2. **Fix** the issue (adjust the change, not bypass the gate)
3. **Re-run** all four gates
4. If the fix cannot be made to pass all gates after 2 attempts:
   - Revert the change: `git checkout -- <files>`
   - Mark the feedback point as "valid but could not apply cleanly"
   - Move to the next point
   - Report the issue in the Phase 4 summary

---

## Rules

- Never skip quality gates
- Never bundle multiple feedback points into one commit
- Never modify code that isn't related to the feedback being addressed
- Always wait for user confirmation after Phase 2 validation
- Always use project commit message conventions
- If a feedback point requires changes in multiple files, that is still ONE commit (one logical change)
