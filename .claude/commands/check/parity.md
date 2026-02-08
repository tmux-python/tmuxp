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

6. **Commit each file separately**

## Key areas to verify

- Check `importers.py` line-by-line against actual tmuxinator/teamocil config keys
- Verify `load_workspace()` actually reads config keys it claims to support
- Cross-reference CHANGELOGs for version-specific features
- Check test fixtures match real-world configs

---

# Import Behavior

Study tmuxp, teamocil, and tmuxinator source code. Find any syntax they support that tmuxp's native syntax doesn't.

Create/update:
- `notes/import-teamocil.md`
- `notes/import-tmuxinator.md`

## Syntax Level Differences / Limitations

For each config key and syntax pattern discovered, classify as:

### Differences (Translatable)

Syntax that differs but can be automatically converted during import. Document the mapping.

### Limitations (tmuxp needs to add support)

Syntax/features that cannot be imported because tmuxp lacks the underlying capability. For each, note:
1. What the feature does in the source tool
2. Why it can't be imported
3. What tmuxp would need to add

---

# WorkspaceBuilder

Analyze what WorkspaceBuilder needs to:

1. **Auto-detect config format** — Determine heuristics to identify tmuxinator vs teamocil vs tmuxp configs transparently
2. **100% feature support** — List every feature/behavior needed for complete compatibility, including behavioral idiosyncrasies
