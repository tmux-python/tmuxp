---
description: Generate CHANGES entries from branch commits and PR context
argument-hint: "[optional additional context about the changes]"
allowed-tools: Bash(git log:*), Bash(git branch:*), Bash(git symbolic-ref:*), Bash(gh pr view:*), Bash(gh pr list:*), Read, Grep, Glob, Edit
---

# Changelog Entry Generator

Generate well-formatted CHANGES entries from the current branch's commits and PR context. This command analyzes commits, categorizes them, and inserts entries into the CHANGES file after user review.

Additional context from user: $ARGUMENTS

---

## Phase 1: Gather Context

**Goal**: Collect all information needed to generate changelog entries.

**Actions**:

1. **Detect project name** from `pyproject.toml`:
   - Read `pyproject.toml` and extract the `name` field under `[project]`
   - This is used for matching the CHANGES heading format (`## <project> vX.Y.Z`)

2. **Detect trunk branch**:
   ```
   git symbolic-ref refs/remotes/origin/HEAD
   ```
   - Strip `refs/remotes/origin/` prefix to get branch name
   - Fall back to `master` if the above fails

3. **Verify not on trunk**:
   - Check current branch: `git branch --show-current`
   - If on trunk, report "Already on trunk branch — nothing to generate" and stop

4. **Read CHANGES file**:
   - Find the CHANGES file (usually `CHANGES` with no extension at project root)
   - Identify the unreleased section heading (e.g., `## vcspull v1.51.x (unreleased)`)
   - Locate the `<!-- END PLACEHOLDER` marker line — this is where new entries are inserted
   - Note any existing entries between `<!-- END PLACEHOLDER -->` and the next `## ` release heading
   - Record which section headings (e.g., `### Bug fixes`, `### Features`) already exist in the unreleased block

5. **Check for PR**:
   ```
   gh pr view --json number,title,body,labels 2>/dev/null
   ```
   - If a PR exists, extract the number, title, body, and labels
   - If no PR exists, note that `(#???)` placeholders will be used

6. **Get commits**:
   ```
   git log <trunk>..HEAD --oneline
   ```
   - Also get full commit details for body parsing:
   ```
   git log <trunk>..HEAD --format='%H %s%n%b---'
   ```
   - If no commits ahead of trunk, report "No commits ahead of trunk" and stop

---

## Phase 2: Categorize Commits

**Goal**: Parse commits into changelog categories and group related ones.

### Commit type mapping

Parse the commit type from the `Component(type[sub])` convention in commit subjects:

| Commit type | CHANGES section | Notes |
|---|---|---|
| `feat` | Features / New features | New functionality |
| `fix` | Bug fixes | Bug fixes |
| `docs` | Documentation | Doc changes |
| `test` | Tests | Test additions/changes |
| `refactor` | (only if user-visible) | Skip internal-only refactors |
| `chore`, `deps` | Development | Maintenance, dependency bumps |
| `style` | (skip) | Formatting-only changes |

### Grouping rules

- **TDD workflow sequences**: An xfail commit + a fix commit + an xfail-removal commit should collapse into a **single** bug fix entry. The fix commit's message is the primary source.
- **Dependency bumps**: A `pyproject` deps commit + a CHANGES doc commit = 1 entry under "Breaking changes" (if it's a minimum version bump) or "Development"
- **Multi-commit features**: Sequential `feat` commits on the same component collapse into one entry
- **Skip entirely**: merge commits, `commands(feat[...])` commits (adding claude commands), lock-only changes, internal-only refactors

### Output of this phase

A structured list of entries grouped by section, each with:
- Section name (e.g., "Bug fixes")
- Entry text (formatted markdown)
- Source commit(s) for traceability

---

## Phase 3: Generate Entries

**Goal**: Write the exact markdown to be inserted into CHANGES.

### Format rules (derived from existing CHANGES files)

1. **Section headings**: Use `### Section Name` (e.g., `### Bug fixes`, `### Features`)

2. **Section order** (only include sections that have entries):
   - Breaking changes
   - Features / New features
   - Bug fixes
   - Documentation
   - Tests
   - Development

3. **Simple entries** — single bullet:
   ```markdown
   - Brief description of the change (#123)
   ```

4. **Detailed entries** — sub-heading with description:
   ```markdown
   #### Component: Brief description (#123)

   Explanatory paragraph about what changed and why.

   - Bullet point with specific detail
   - Another detail
   ```

5. **PR references**:
   - If PR number is known: `(#512)`
   - If no PR exists: `(#???)`

6. **Match existing style**:
   - Check whether the project uses "Bug fixes" or "Bug Fixes" (match existing capitalization)
   - Check whether "Features" or "New features" is used
   - Preserve the project's conventions

### Entry writing guidelines

- Write from the user's perspective — what changed for them, not internal implementation details
- Lead with the *what*, not the *why* (the description paragraph handles *why*)
- Use present tense for the entry title ("Add support for..." not "Added support for...")
- Don't repeat the section heading in the entry text
- Keep bullet entries to 1-2 lines; use the sub-heading format for anything needing more explanation

---

## Phase 4: Present for Review

**CRITICAL**: This is a mandatory confirmation gate. Never skip to Phase 5 without explicit user approval.

**Present to the user**:

1. **Summary line**:
   ```
   Branch: <branch-name> | Commits: <count> | PR: #<number> (or "none")
   ```

2. **Proposed entries** in a fenced code block showing the exact markdown:
   ````
   ```markdown
   ### Bug fixes

   - Fix phantom "None" message when syncing path-based patterns (#512)

   #### cli/sync: Report errored git syncs in summary (#512)

   `update_repo()` now detects and reports git sync failures instead of
   silently succeeding. The sync summary shows errored repositories
   alongside successful and failed counts.
   ```
   ````

3. **Insertion point**: Describe where these entries will go:
   ```
   Insert after: <!-- END PLACEHOLDER - ADD NEW CHANGELOG ENTRIES BELOW THIS LINE -->
   Before: (next release heading or existing unreleased entries)
   ```

4. **Ask the user**: "Insert these entries into CHANGES? You can also ask me to modify them first."

**Wait for user response.** Do not proceed until they confirm.

---

## Phase 5: Insert into CHANGES

**Goal**: Insert the approved entries into the CHANGES file.

**Only execute after explicit user approval in Phase 4.**

### Insertion logic

1. **Find the insertion point**: Locate the `<!-- END PLACEHOLDER` line in the CHANGES file

2. **Check for existing unreleased section headings**:
   - If the CHANGES file already has a `### Bug fixes` section in the unreleased block, and the new entries also have bug fixes, **append** to the existing section rather than creating a duplicate heading
   - If the section doesn't exist yet, insert the full section with heading

3. **Insert the entries**:
   - Use the Edit tool to insert after the `<!-- END PLACEHOLDER -->` line
   - Ensure exactly one blank line between the placeholder comment and the first section heading
   - Ensure exactly one blank line between sections

4. **Show the result**:
   - After editing, read the modified region of the CHANGES file and display it so the user can verify
   - Note: this command does NOT commit — the user decides when to stage and commit the CHANGES update

### Edge case: merging with existing entries

If there are already entries below the placeholder in the unreleased section:

- New entries for **existing sections** are appended at the end of that section (before the next `###` heading or the next `## ` release heading)
- New entries for **new sections** follow the section order defined in Phase 3 — insert the new section in the correct position relative to existing sections
- Never duplicate a `###` section heading
