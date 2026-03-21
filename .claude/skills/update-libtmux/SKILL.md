---
name: update-libtmux
description: >-
  Use when the user asks to "update libtmux", "bump libtmux",
  "upgrade libtmux dependency", "check for new libtmux version",
  or when investigating whether tmuxp needs a libtmux update.
  Guides the full workflow: studying upstream changes, updating
  the dependency, migrating code and tests, and producing
  separate atomic commits with rich messages.
user-invocable: true
argument-hint: "[target-version] (optional, defaults to latest on PyPI)"
---

# Update libtmux Dependency

Workflow for updating the libtmux dependency in tmuxp with separate, atomic commits.

## Overview

This skill produces up to four atomic commits on a dedicated branch, then opens a PR:

1. **Package commit** — bump `pyproject.toml` + `uv.lock`
2. **Code commit(s)** — API migrations, new feature adoption (if needed)
3. **Test commit(s)** — test updates for changed/new APIs (if needed)
4. **CHANGES commit** — changelog entry documenting the bump

Each commit stands alone, passes tests independently, and has a rich commit body.

## Step 0: Preflight

Gather current state before making any changes.

### 0a. Current dependency

Read `pyproject.toml` and find the `libtmux~=X.Y.Z` specifier in `[project] dependencies`.

### 0b. Latest version on PyPI

```bash
pip index versions libtmux
```

If the user provided a target version, use that. Otherwise use the latest from PyPI.

### 0c. Short-circuit check

If the current specifier already covers the target version, inform the user and stop.

### 0d. Ensure local libtmux clone is current

The local libtmux clone lives at `~/work/python/libtmux`. Fetch and check:

```bash
cd ~/work/python/libtmux && git fetch --tags && git log --oneline -5
```

Verify the target version tag exists. If not, the version may not be released yet — warn the user.

## Step 1: Study upstream changes

This is the most important step. Read the libtmux CHANGES file to understand what changed between the current pinned version and the target.

### 1a. Read libtmux CHANGES

Read `~/work/python/libtmux/CHANGES` from the section for the target version back through all versions since the current pin.

Categorize changes into:

| Category | Action needed in tmuxp |
|----------|----------------------|
| **Breaking changes** | Must fix code/tests |
| **Deprecations** | Should migrate away |
| **New APIs** | Optionally adopt |
| **Bug fixes** | Note for commit message |
| **Internal/docs** | Note for commit message only |

### 1b. Check for API impact in tmuxp

For each breaking change or deprecation, grep tmuxp source and tests:

```bash
# Example: if Window.rename_window() changed signature
rg "rename_window" src/ tests/
```

Search patterns to check (adapt based on actual changes):
- Method/function names that changed
- Constructor parameters that changed
- Import paths that moved
- Exception types that changed
- Return type changes

### 1c. Check libtmux git log for details

For breaking changes where the CHANGES entry is unclear, read the actual commits:

```bash
cd ~/work/python/libtmux && git log --oneline v{CURRENT}..v{TARGET} -- src/
```

### 1d. Summarize findings

Present findings to the user before proceeding:
- Versions being skipped (e.g., "0.53.1, 0.54.0, 0.55.0")
- Breaking changes requiring code updates
- New APIs available for adoption
- Test impact assessment
- Estimated commit count

Get user confirmation to proceed.

## Step 2: Create branch

```bash
git checkout -b deps/libtmux-{TARGET_VERSION}
```

Branch naming convention: `deps/libtmux-X.Y.Z`

## Step 3: Package commit

Update the dependency specifier and lock file.

### 3a. Edit pyproject.toml

Change the `libtmux~=X.Y.Z` line in `[project] dependencies`.

### 3b. Update lock file

```bash
uv lock
```

### 3c. Verify installation

```bash
uv sync
```

### 3d. Run tests (smoke check)

```bash
uv run py.test tests/ -x -q 2>&1 | tail -20
```

Note any failures — these indicate code changes needed in Step 4.

### 3e. Commit

Commit message format (use heredoc for multiline):

```
deps(libtmux[~=X.Y.Z]): Bump from ~=A.B.C

why: Pick up N libtmux release(s) (list versions) bringing
[brief summary of key changes].

what:
- Bump libtmux dependency specifier ~=A.B.C -> ~=X.Y.Z in pyproject.toml
- Update uv.lock

libtmux X.Y.Z (date):
- [key change 1]
- [key change 2]

[repeat for each intermediate version]

Release: https://github.com/tmux-python/libtmux/releases/tag/vX.Y.Z
Changelog: https://libtmux.git-pull.com/history.html#libtmux-X-Y-Z-YYYY-MM-DD
```

Stage only `pyproject.toml` and `uv.lock`.

## Step 4: Code commit(s) — if needed

Skip this step if no breaking changes or API migrations are needed.

### 4a. Fix breaking changes

Address each breaking change identified in Step 1b. Make minimal, targeted fixes.

### 4b. Adopt new APIs (optional)

Only if the user requested it or it simplifies existing code significantly.

### 4c. Run linting and type checking

```bash
uv run ruff check . --fix --show-fixes
uv run ruff format .
uv run mypy
```

### 4d. Run tests

```bash
uv run py.test tests/ -x -q
```

### 4e. Commit

One commit per logical change. Format:

```
Scope(type[detail]): description of the migration

why: libtmux X.Y.Z changed [what changed].
what:
- [specific code change 1]
- [specific code change 2]
```

Use the project's standard scope conventions:
- `workspace/builder(fix[method])` for builder changes
- `cli/load(fix[feature])` for CLI changes
- `plugin(fix[hook])` for plugin changes

## Step 5: Test commit(s) — if needed

Skip if no test changes are required beyond what was fixed in Step 4.

### 5a. Update tests for API changes

Fix any tests that broke due to upstream changes.

### 5b. Add tests for newly adopted APIs

If Step 4 adopted new libtmux features, add tests.

### 5c. Run full test suite

```bash
uv run py.test
```

All tests must pass (doctests included — pytest is configured with `--doctest-modules`).

### 5d. Commit

```
tests(scope[detail]): description

why: Adapt tests for libtmux X.Y.Z [change].
what:
- [specific test change 1]
- [specific test change 2]
```

## Step 6: CHANGES commit

### 6a. Determine placement

The CHANGES file has a placeholder section for the next unreleased version at the top. Add the entry below the placeholder comments.

### 6b. Write the entry

Add under `### Breaking Changes` if the bump changes minimum version, or `### Development` / `### Dependencies` for non-breaking bumps:

For a breaking bump:

```markdown
#### **libtmux** minimum bumped from `~=A.B.C` to `~=X.Y.Z`

  Picks up N releases: [version list with brief descriptions].
```

For a non-breaking bump, use `### Dependencies`:

```markdown
### Dependencies

- Bump libtmux `~=A.B.C` -> `~=X.Y.Z` ([key changes summary])
```

### 6c. Commit

```
docs(CHANGES): libtmux ~=A.B.C -> ~=X.Y.Z

why: Document the dependency bump for the upcoming release.
what:
- Add entry for libtmux bump under [section name]
- Summarize key upstream changes
```

## Step 7: Push and open PR

### 7a. Push the branch

```bash
git push -u origin deps/libtmux-{TARGET_VERSION}
```

### 7b. Open PR

```bash
gh pr create \
  --title "deps(libtmux[~=X.Y.Z]): Bump from ~=A.B.C" \
  --body "$(cat <<'EOF'
## Summary

- Bump libtmux from `~=A.B.C` to `~=X.Y.Z`
- [N] upstream releases included
- [Breaking changes summary, or "No breaking changes"]

## Upstream changes

### libtmux X.Y.Z (date)
- [changes]

[repeat for intermediate versions]

## Changes in this PR

- **Package**: pyproject.toml + uv.lock
- **Code**: [summary or "No code changes needed"]
- **Tests**: [summary or "No test changes needed"]
- **CHANGES**: Documented bump

## Test plan

- [ ] `uv run py.test` passes
- [ ] `uv run mypy` passes
- [ ] `uv run ruff check .` passes
EOF
)"
```

### 7c. Report to user

Provide the PR URL and a summary of all commits created.

## Reference: Past libtmux bumps

These exemplar commits show the established patterns:

| Version bump | Deps commit | CHANGES commit | PR |
|---|---|---|---|
| 0.53.0 → 0.55.0 | `ff52d0d2` | `094800f4` | #1019 |
| 0.52.1 → 0.53.0 | `5ff6400f` | `240d85fe` | #1003 |
| 0.51.0 → 0.52.1 | `fabd678f` | (in same commit) | #1001 |
| 0.50.1 → 0.51.0 | (in merge) | (in merge) | #999 |

The 0.53→0.55 bump (`ff52d0d2`) is the gold standard for commit message richness — per-version changelogs, upstream links, and clear why/what structure.

## Checklist

Use this as a progress tracker:

- [ ] Preflight: identify current and target versions
- [ ] Study upstream CHANGES and identify impact
- [ ] Summarize findings and get user confirmation
- [ ] Create branch `deps/libtmux-X.Y.Z`
- [ ] Package commit: pyproject.toml + uv.lock
- [ ] Code commit(s): API migrations (if needed)
- [ ] Test commit(s): test updates (if needed)
- [ ] CHANGES commit: changelog entry
- [ ] Push and open PR
- [ ] Report PR URL to user
