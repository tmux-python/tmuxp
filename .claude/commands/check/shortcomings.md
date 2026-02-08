# /check:shortcomings — API Limitations Analysis

Second-step command that reads parity analysis and outputs API blockers to `notes/plan.md`.

## Input Files (from /check:parity)

- `notes/parity-tmuxinator.md`
- `notes/parity-teamocil.md`
- `notes/import-tmuxinator.md`
- `notes/import-teamocil.md`

## Workflow

1. **Read parity analysis files** to understand feature gaps

2. **Explore libtmux** at `~/work/python/libtmux/`:
   - What APIs are missing? (e.g., no `pane.set_title()`)
   - What's hardcoded? (e.g., `shutil.which("tmux")`)

3. **Explore tmuxp** at `~/work/python/tmuxp/`:
   - What config keys are dead data?
   - What keys are missing from loader/builder?
   - What CLI flags are missing?

4. **Update `notes/plan.md`** with:
   - libtmux limitations (what Server/Pane/Window/Session can't do)
   - tmuxp limitations (what WorkspaceBuilder/loader/cli can't do)
   - Dead config keys (imported but ignored)
   - Required API additions for each gap
   - Non-breaking implementation notes

5. **Commit** `notes/plan.md`

## Output Structure

notes/plan.md should follow this format:

### libtmux Limitations
Per-limitation:
- **Blocker**: What API is missing/hardcoded
- **Blocks**: What parity feature this prevents
- **Required**: What API addition is needed

### tmuxp Limitations
Per-limitation:
- **Blocker**: What's missing/broken
- **Blocks**: What parity feature this prevents
- **Required**: What change is needed

### Implementation Notes
Non-breaking approach for each limitation.
