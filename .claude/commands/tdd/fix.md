---
description: TDD bug-fix workflow -- reproduce a bug as a failing test, find root cause, fix, and verify
argument-hint: Paste or describe the bug to reproduce and fix
---

# TDD Bug-Fix Workflow

You are an expert test engineer performing a disciplined TDD bug-fix loop on this project. Follow this workflow precisely for every bug.

Initial bug report: $ARGUMENTS

---

## Phase 1: Understand the Bug

**Goal**: Parse the bug report into a testable reproduction scenario.

**Actions**:
1. Create a todo list tracking all phases
2. Read the bug report and identify:
   - **Symptom**: What the user observes (error message, wrong output, silent failure)
   - **Expected behavior**: What should happen instead
   - **Trigger conditions**: What inputs, configuration, or state reproduce it
   - **Affected component**: Which module/function is involved
3. Use Explore agents to find the relevant source code and existing tests:
   - The test file that covers this area
   - The source file with the suspected bug
   - Any existing fixtures that can help reproduce the scenario
4. Read the identified files to understand current behavior
5. Summarize your understanding of the bug and confirm with user before proceeding

---

## Phase 2: Write a Failing Test (xfail)

**Goal**: Create a test that reproduces the bug and is expected to fail.

**CRITICAL RULES** (from project's CLAUDE.md):
- Write **functional tests only** -- standalone `test_*` functions, NOT classes
- Use `typing.NamedTuple` for parameterized tests when appropriate
- Use `from __future__ import annotations` at top of file
- Use `import typing as t` namespace style for stdlib
- Leverage project-specific fixtures from conftest.py
- Document every mock with comments explaining WHAT is being mocked and WHY

**Actions**:
1. Identify which test file to add the test to
2. Study existing test patterns in that file (parameter fixtures, assertion styles, imports)
3. Write a test function that:
   - Has a descriptive name: `test_<component>_<bug_description>`
   - Has a docstring explaining the bug scenario
   - Uses existing fixtures wherever possible
   - Is decorated with `@pytest.mark.xfail(strict=True)` so it's expected to fail
   - Asserts the **correct** (expected) behavior, not the buggy behavior
4. Run the test to confirm it fails as expected:
   ```
   uv run pytest <test_file>::<test_name> -xvs
   ```
5. Run the full test suite to ensure no other tests broke:
   ```
   uv run pytest <test_file> -q
   ```
6. Run linting and type checks:
   ```
   uv run ruff format .
   uv run ruff check . --fix --show-fixes
   uv run mypy
   ```
7. **Commit the failing test** using project commit style:
   ```
   tests(feat[<test_file>]) Add xfail test for <bug description>

   why: <Why this test is needed -- what behavior is broken>
   what:
   - Add test_<name> with @pytest.mark.xfail(strict=True)
   - <What the test sets up and asserts>
   ```

---

## Phase 3: Find the Root Cause

**Goal**: Trace from symptom to the exact code that needs to change.

**Actions**:
1. Read the source code path exercised by the test
2. Add temporary debug logging if needed (but track it for cleanup)
3. Identify the root cause -- the specific line(s) or logic gap
4. If the bug spans multiple packages (this project + a dependency):
   - Note which package each change belongs to
   - Check that the dependency is installed as editable from local source:
     ```
     uv run python -c "import <dep>; print(<dep>.__file__)"
     ```
   - If it points to `.venv/lib/.../site-packages/`, the editable install is stale -- fix it:
     ```
     # In pyproject.toml [tool.uv.sources]:
     # Temporarily use: <dep> = { path = "/path/to/<dep>", editable = true }
     # Then: uv lock && uv sync
     ```
5. Document the root cause clearly

---

## Phase 4: Fix the Bug

**Goal**: Apply the minimal fix that makes the test pass.

**Principles**:
- Minimal change -- only fix what's broken
- Don't refactor surrounding code
- Don't add features beyond the fix
- Follow existing code patterns and style
- Use `import typing as t` namespace style
- Use NumPy docstring style if adding/modifying docstrings

**Actions**:
1. Apply the fix to the source code
2. Remove any debug instrumentation added in Phase 3
3. Run the failing test (it should still fail because xfail is still on):
   ```
   uv run pytest <test_file>::<test_name> -xvs
   ```
   - If it now passes, the xfail decorator will cause it to XPASS (unexpected pass) -- this is correct!
4. Run quality checks:
   ```
   uv run ruff format .
   uv run ruff check . --fix --show-fixes
   uv run mypy
   ```
5. **Commit the fix** using project commit style:
   ```
   <component>(fix[<subcomponent>]) <Concise description>

   why: <Root cause explanation>
   what:
   - <Specific technical changes>
   ```

---

## Phase 5: Remove xfail and Verify

**Goal**: Confirm the fix works and the test is a proper regression test.

**Actions**:
1. Remove `@pytest.mark.xfail(strict=True)` from the test
2. Update the test docstring to describe it as a regression test (not a bug report)
3. Run the test -- it MUST pass:
   ```
   uv run pytest <test_file>::<test_name> -xvs
   ```
4. Run the FULL test suite:
   ```
   uv run pytest <test_file> -q
   ```
5. Run all quality checks:
   ```
   uv run ruff format .
   uv run ruff check . --fix --show-fixes
   uv run mypy
   ```
6. If ALL checks pass, **commit**:
   ```
   tests(fix[<test_file>]) Remove xfail from <test_name>

   why: Fix verified -- <brief description of what was fixed>
   what:
   - Remove @pytest.mark.xfail(strict=True)
   - Update docstring to describe as regression test
   ```

---

## Phase 6: Recovery Loop (if fix doesn't work)

**Goal**: If the test still fails after the fix, diagnose why.

**Decision tree**:

### A. Is the reproduction genuine?
1. Read the test carefully -- does it actually reproduce the reported bug?
2. Run the test with `-xvs` and examine the output
3. If the test is testing the wrong thing:
   - Go back to **Phase 2** and rewrite the test
   - Recommit with an amended failing test

### B. Is the fix correct?
1. Add debug logging to trace execution through the fix
2. Check if the fix is actually being executed (stale installs are common with uv):
   ```
   uv run python -c "import <module>; import inspect; print(inspect.getsource(<function>))"
   ```
3. If the installed code doesn't match the source:
   - Check `uv.lock` and `[tool.uv.sources]` in pyproject.toml
   - Force reinstall: `uv pip install -e /path/to/dependency`
   - Verify: the `__file__` path should point to the source directory
4. If the fix is wrong:
   - Revert the fix
   - Go back to **Phase 3** to re-analyze the root cause
   - Apply a new fix in **Phase 4**

### C. Loop limit
- After 3 failed fix attempts, stop and present findings to the user:
  - What was tried
  - What the debug output shows
  - What the suspected issue is
  - Ask for guidance

---

## Cross-Dependency Workflow

When the bug involves both this project and a dependency:

1. **Dependency changes first**: Fix the underlying library
2. **Commit in the dependency**: Use the same commit style
3. **Verify dependency tests**:
   ```
   cd /path/to/<dep> && uv run pytest tests/ -q
   ```
4. **Update this project's dependency reference**: Ensure this project uses the fixed dependency
5. **Then fix/test in this project**

**IMPORTANT**: `uv run` enforces the lockfile. If `[tool.uv.sources]` points to a git remote, `uv run` will overwrite any local `uv pip install -e`. To develop across repos simultaneously, temporarily change `[tool.uv.sources]` to a local path.

---

## Quality Gates (every commit must pass)

Before EVERY commit, run this checklist:
```
uv run ruff format .
uv run ruff check . --fix --show-fixes
uv run mypy
uv run pytest <test_file> -q
```

ALL must pass. A commit with failing tests or lint errors is not acceptable.

---

## Commit Message Format

```
Component/File(commit-type[Subcomponent/method]) Concise description

why: Explanation of necessity or impact.
what:
- Specific technical changes made
- Focused on a single topic
```

Use HEREDOC for multi-line messages:
```bash
git commit -m "$(cat <<'EOF'
Component(type[sub]) Description

why: Reason
what:
- Change 1
- Change 2
EOF
)"
```
