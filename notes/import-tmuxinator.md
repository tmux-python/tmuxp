# Tmuxinator Import Behavior

Analysis of `import_tmuxinator()` in `src/tmuxp/workspace/importers.py:8-102`.

## Syntax Differences (Translatable)

### Key renames that ARE handled

| tmuxinator key | tmuxp key | Lines |
|----------------|-----------|-------|
| `project_name` | `session_name` | 24-25 |
| `name` | `session_name` | 26-27 |
| `project_root` | `start_directory` | 31-32 |
| `root` | `start_directory` | 33-34 |
| `tabs` | `windows` | 56-57 |
| `cli_args` (extracts `-f`) | `config` | 36-42 |
| `tmux_options` (extracts `-f`) | `config` | 43-49 |
| `socket_name` | `socket_name` | 51-52 |
| window `pre` | `shell_command_before` | 92-93 |
| window `root` | `start_directory` | 96-97 |
| window `layout` | `layout` | 99-100 |
| window `panes` | `panes` | 94-95 |

### Key renames that are NOT handled

| tmuxinator key | Should map to | Notes |
|----------------|---------------|-------|
| `rvm` | `shell_command_before` + `rvm use X` | Only `rbenv` handled (lines 72-77) |
| `post` | — | No equivalent; should emit warning |
| `startup_window` | Find window by name/index → `focus: true` | tmuxp uses different syntax |
| `startup_pane` | Set `focus: true` on pane | tmuxp uses different syntax |
| `attach: false` | — | No config key in tmuxp |
| `socket_path` | — | tmuxp has `-S` CLI but no config key |
| `tmux_command` | — | No equivalent (libtmux hardcoded to `tmux`) |
| `synchronize` | `options_after: {synchronize-panes: on}` | Not a first-class key |
| `enable_pane_titles` | — | No equivalent |
| `pane_title_position` | — | No equivalent |
| `pane_title_format` | — | No equivalent |
| `on_project_start` | — | No equivalent (requires plugin API) |
| `on_project_first_start` | — | No equivalent |
| `on_project_restart` | — | No equivalent |
| `on_project_exit` | — | No equivalent |
| `on_project_stop` | — | No equivalent |

### Shorthand expansions

| tmuxinator syntax | tmuxp expansion | Lines |
|-------------------|-----------------|-------|
| `pre: "cmd"` (string) | `shell_command_before: ["cmd"]` | 62-63, 67-68 |
| `pre: [a, b]` (list) | `shell_command_before: [a, b]` | 64-65, 69-70 |
| `rbenv: "2.0.0"` | `shell_command_before` += `rbenv shell 2.0.0` | 72-77 |
| `- name: "cmd"` (window shorthand) | `{window_name: name, panes: ["cmd"]}` | 83-86 |
| `- name: [a, b]` (window with list) | `{window_name: name, panes: [a, b]}` | 87-90 |

---

## Limitations (tmuxp needs to add support)

### Features that can't be imported because tmuxp lacks capability

| Feature | tmuxinator location | Notes |
|---------|---------------------|-------|
| Lifecycle hooks (`on_project_*`) | `lib/tmuxinator/hooks/project.rb` | tmuxp has plugin hooks (Python API), not shell commands in config |
| Pane titles | `lib/tmuxinator/project.rb:384-419` | No pane title support in tmuxp |
| `tmux_command` (wemux, byobu) | `lib/tmuxinator/project.rb:199-201` | libtmux hardcodes `tmux` binary |
| `attach: false` in config | `lib/tmuxinator/project.rb:170-173` | tmuxp has CLI `-d` only |
| ERB templating | `lib/tmuxinator/project.rb:43-70` | tmuxp has env vars only, no arg passing |
| `--no-pre-window` flag | `lib/tmuxinator/project.rb:176` | No equivalent CLI flag |

### Dead data (imported but ignored)

| Key | Imported at | Problem |
|-----|-------------|---------|
| `socket_name` | Line 51-52 | `load_workspace()` never reads this from config; it only accepts `socket_name` as CLI parameter. See `src/tmuxp/cli/load.py:369-374`. |
| Non-`-f` flags from `cli_args`/`tmux_options` | Lines 36-49 | Only `-f` is extracted; other flags (e.g., `-2`, `-u`) are stripped and lost. |

---

## Importer Code Issues

### 1. Loop variable reassignment bug (line 80-81)

```python
for window_dict in workspace_dict["windows"]:
    for k, v in window_dict.items():
        window_dict = {"window_name": k}  # reassigns loop variable!
```

This only works because tmuxinator windows are **single-key hashes** like `- editor: {...}`. The inner `for k, v` loop iterates once, and the immediate reassignment of `window_dict` happens to work.

**Bug**: If a tmuxinator window has multiple top-level keys (malformed or alternative syntax), only the first key is processed. Example:

```yaml
windows:
  - editor:
      panes: [vim]
    layout: main-vertical  # This key is SILENTLY IGNORED
```

### 2. Mutating input dict (throughout)

Uses `dict.pop()` at lines 25, 27, 32, 34, 57 — destructively modifies the input dict. If the caller reuses the dict, data is lost.

### 3. Missing `rvm` support (only `rbenv`)

tmuxinator supports both `rbenv` and `rvm` at `lib/tmuxinator/project.rb:331-341`:

```ruby
def rbenv?
  yaml["rbenv"]
end

def rvm?
  yaml["rvm"]
end
```

But the importer only handles `rbenv` (lines 72-77). `rvm` config keys are silently ignored.

### 4. No named pane support

tmuxinator supports named panes via hash syntax:

```yaml
panes:
  - editor: vim
  - server: rails s
```

Where `editor` becomes the pane title (`lib/tmuxinator/window.rb:59-66`):

```ruby
def build_panes(panes_yml)
  Array(panes_yml).map.with_index do |pane_yml, index|
    commands, title = case pane_yml
                      when Hash
                        [pane_yml.values.first, pane_yml.keys.first]  # title from key!
```

The importer extracts commands but loses the title (no tmuxp equivalent anyway).

### 5. Minimal test coverage

Only 3 test fixtures exist (`tests/fixtures/import_tmuxinator/test1-3.yaml`). Missing tests for:
- `synchronize`
- `startup_window` / `startup_pane`
- `attach: false`
- Named panes (`- title: cmd`)
- Lifecycle hooks
- `rvm` config
- `socket_path`
- `tmux_command`
- Edge cases (empty windows, null values)

---

## Test Fixture Analysis

### test1.yaml — Basic window formats

Tests window shorthand syntax:
- `- editor:` with nested config
- `- server: bundle exec rails s` (single command)
- `- logs: tail -f ...` (single command)

### test2.yaml — Legacy format

Tests deprecated keys:
- `project_name` (deprecated → `name`)
- `project_root` (deprecated → `root`)
- `tabs` (deprecated → `windows`)
- `cli_args` (deprecated → `tmux_options`)
- `rbenv` (deprecated → `pre_window`)

### test3.yaml — Modern format

Tests current recommended syntax:
- `name` instead of `project_name`
- `root` instead of `project_root`
- `windows` instead of `tabs`
- `tmux_options` instead of `cli_args`
- `pre_window` directly (not `rbenv`)
- Window-level `root` override

---

## Summary

| Category | Count |
|----------|-------|
| Keys handled correctly | 12 |
| Keys not handled (could be) | 3 (`rvm`, `startup_window`, `startup_pane`, `synchronize`) |
| Keys not handled (tmuxp lacks feature) | 10 |
| Dead data (imported but ignored) | 2 (`socket_name`, non-`-f` CLI args) |
| Code bugs | 2 (loop reassignment, input mutation) |
