# /check:parity — Feature Parity Analysis

Deep-dive analysis of tmuxp vs tmuxinator and teamocil. Updates comparison docs and parity notes.

## Workflow

1. **Read source code** of all three projects:
   - tmuxp: `src/tmuxp/workspace/` (builder.py, loader.py, importers.py), `src/tmuxp/cli/load.py`
   - tmuxinator: `~/study/ruby/tmuxinator/lib/tmuxinator/` (project.rb, window.rb, pane.rb, hooks/, assets/template.erb)
   - teamocil: `~/study/ruby/teamocil/lib/teamocil/tmux/` (session.rb, window.rb, pane.rb)

2. **Read existing docs** for baseline:
   - `docs/about.md` — tmuxp's own feature description
   - `docs/comparison.md` — feature comparison table (create if missing)
   - `notes/parity-tmuxinator.md` — tmuxinator parity analysis (create if missing)
   - `notes/parity-teamocil.md` — teamocil parity analysis (create if missing)

3. **Update `docs/comparison.md`** with tabular feature comparison:
   - Overview table (language, min tmux, config format, architecture)
   - Configuration keys table (every key across all three, with ✓/✗)
   - CLI commands table (side-by-side)
   - Architecture comparison (ORM vs script generation vs command objects)
   - Include version numbers for each project

4. **Update `notes/parity-tmuxinator.md`** with:
   - Features tmuxinator has that tmuxp lacks (with source locations)
   - Import behavior analysis (what the current importer handles vs misses)
   - WorkspaceBuilder requirements for 100% feature support
   - Code quality issues in current importer

5. **Update `notes/parity-teamocil.md`** with:
   - Features teamocil has that tmuxp lacks (with source locations)
   - v0.x vs v1.4.2 format differences (current importer targets v0.x only)
   - Import behavior analysis
   - WorkspaceBuilder requirements for full parity

6. **Commit each file separately**:
   - `docs/comparison.md` — "docs(comparison): Update feature comparison table vs tmuxinator and teamocil"
   - `notes/parity-tmuxinator.md` — "notes(parity): Update tmuxinator feature parity analysis"
   - `notes/parity-teamocil.md` — "notes(parity): Update teamocil feature parity analysis"

## Key areas to verify

- Check `importers.py` line-by-line against actual tmuxinator/teamocil config keys
- Verify `load_workspace()` actually reads config keys it claims to support (e.g., `socket_name` is dead data)
- Cross-reference CHANGELOGs for version-specific features
- Check test fixtures match real-world configs
