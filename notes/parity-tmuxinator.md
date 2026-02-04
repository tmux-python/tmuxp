# Tmuxinator Feature Parity Analysis

What tmuxinator (v3.3.7) has that tmuxp currently lacks, with import gap analysis and
WorkspaceBuilder requirements.

## Features tmuxinator has that tmuxp lacks

### A. Configuration Features

#### 1. Project hooks (shell commands in config)

tmuxinator supports 5 lifecycle hooks as shell commands directly in the YAML config:

- `on_project_start` — runs on every `tmuxinator start`
- `on_project_first_start` — runs only when session doesn't exist yet
- `on_project_restart` — runs when reattaching to existing session
- `on_project_exit` — runs on session exit/detach
- `on_project_stop` — runs on `tmuxinator stop`

**Location**: `lib/tmuxinator/hooks/project.rb:1-45`, `lib/tmuxinator/assets/template.erb` lines 14, 21, 99, 114

**tmuxp equivalent**: Plugin hooks exist (`before_workspace_builder`, `on_window_create`, `after_window_finished`, `before_script`, `reattach`) but these are Python class methods, not shell commands in YAML. tmuxp has `before_script` as a config key but no exit/stop hooks.

**Gap**: tmuxp needs shell command hooks in workspace config YAML, not just the plugin API.

#### 2. Pane synchronization (`synchronize`)

Enables `set-window-option synchronize-panes on` for a window.

- `synchronize: before` — sync before sending commands (deprecated in tmuxinator)
- `synchronize: after` — sync after commands complete (preferred)
- `synchronize: true` — alias for `after`

**Location**: `lib/tmuxinator/window.rb:35-37,129-148`

**tmuxp workaround**: Can be achieved via `options_after: {synchronize-panes: on}` but is not a first-class config key.

#### 3. Pane titles

Per-pane titles and window-level border settings:

- `enable_pane_titles: true` — session level
- `pane_title_position: top|bottom|off` — session level
- `pane_title_format: "..."` — session level
- Named panes via hash key: `- my_title: [cmd1, cmd2]`

**Location**: `lib/tmuxinator/project.rb:384-419`, `lib/tmuxinator/window.rb:59-66`

**tmuxp equivalent**: None. No pane title support in config.

#### 4. Startup window/pane selection

- `startup_window` — select specific window by name or index after load
- `startup_pane` — select specific pane by index within that window

**Location**: `lib/tmuxinator/project.rb:261-267`

**tmuxp equivalent**: Uses `focus: true` on windows/panes — functionally equivalent but different syntax. The importer should map `startup_window` → find matching window and set `focus: true`.

#### 5. Attach control in config (`attach: false`)

Config-level control over whether to auto-attach after loading.

**Location**: `lib/tmuxinator/project.rb:170-173`

**tmuxp equivalent**: CLI flag `-d`/`--detached` only. No in-config `attach` key.

#### 6. Socket path as config key

- `socket_name` — maps to `tmux -L`
- `socket_path` — maps to `tmux -S`

Both are in-config YAML keys in tmuxinator.

**Location**: `lib/tmuxinator/project.rb:228-234`

**tmuxp equivalent**: Has `-L`/`-S` CLI flags (`load.py:476-488`) but no `socket_path` config key in YAML. Note: the tmuxinator importer maps `socket_name` into the tmuxp config at `importers.py:51-52`, but `load_workspace()` in `load.py:369-374` takes `socket_name` only as a CLI parameter and passes it to `Server()` — it never reads `socket_name` from the config dict. So `socket_name` in tmuxp YAML is **dead data** that gets silently ignored.

#### 7. tmux command override (`tmux_command`)

Use alternative tmux-compatible binaries like `wemux` or `byobu`.

**Location**: `lib/tmuxinator/project.rb:199-201`, `lib/tmuxinator/wemux_support.rb`

**tmuxp equivalent**: None. libtmux's `Server` is hardcoded to use `tmux`.

#### 8. tmux CLI options in config (`tmux_options`/`cli_args`)

Pass arbitrary flags to the tmux command via a YAML config key.

**Location**: `lib/tmuxinator/project.rb:237-245`

**tmuxp equivalent**: Has `-f` CLI flag for config file, `-L`/`-S` for sockets, `-2`/`-8` for colors — but these are all CLI-only, not in-config keys. The importer partially handles this by extracting `-f` from the `tmux_options` string (`importers.py:36-49`).

#### 9. ERB templating with arguments

```
tmuxinator start project arg1 key=value
```

Config uses `<%= @args[0] %>`, `<%= @settings["key"] %>`.

**Location**: `lib/tmuxinator/project.rb:43-70`

**tmuxp equivalent**: Environment variable expansion only (`$VAR`, `~`). No argument passing to config files.

**Import feasibility**: ERB is a full Ruby templating engine — not feasible to import ERB syntax. However, tmuxp can implement equivalent functionality with simpler syntax.

##### Implementation Strategy: CLI Argument Passing

tmuxp can support argument passing using the standard Unix `--` separator and `${...}` placeholder syntax (which already exists for env vars):

**CLI syntax:**
```bash
tmuxp load config.yaml -- /path/to/dir name=myproject
```

**Config syntax:**
```yaml
session_name: ${name}
start_directory: ${1}
windows:
  - window_name: editor
    panes:
      - vim ${1}/src
```

**argparse approach:**

The challenge is that argparse doesn't treat `--` as a separator between two positional argument groups. With `nargs="+"` for workspace files, everything gets consumed.

**Solution**: Pre-process `sys.argv` before argparse:

```python
def split_args_at_separator(args: list[str]) -> tuple[list[str], list[str]]:
    """Split CLI args at -- separator."""
    if "--" not in args:
        return args, []
    idx = args.index("--")
    return args[:idx], args[idx + 1:]
```

Then in `cli()`:
```python
command_args, cli_args = split_args_at_separator(sys.argv[1:])
args = parser.parse_args(command_args)
args.cli_args = cli_args  # Attach for load command to use
```

**Substitution approach:**

New functions in `loader.py`:

1. `parse_cli_args(args)` — Convert `["/path", "name=val"]` to `{"1": "/path", "name": "val"}`
2. `substitute_cli_args(config, context)` — Replace `${key}` placeholders recursively

Substitution runs BEFORE `expandshell()` so that:
- CLI args like `${1}`, `${name}` get replaced first
- Remaining `${HOME}`, `${USER}` pass through to env var expansion

**Precedence**: CLI args override env vars with same name.

#### 10. Named panes (pane titles via hash key)

```yaml
panes:
  - editor: vim
  - server: rails s
```

The hash key becomes the pane title.

**Location**: `lib/tmuxinator/window.rb:59-66`

**tmuxp equivalent**: None.

#### 11. `--no-pre-window` flag

Skip `pre_window` commands on startup.

**Location**: `lib/tmuxinator/project.rb:176`, `lib/tmuxinator/cli.rb`

**tmuxp equivalent**: None.

### B. CLI Features

#### 12. Debug/dry-run (`tmuxinator debug`)

Shows generated shell script without executing.

**tmuxp equivalent**: None.

#### 13. Config copy (`tmuxinator copy src dst`)

Copy an existing config to a new name.

**tmuxp equivalent**: None.

#### 14. Stop session (`tmuxinator stop`, `stop-all`)

Kill session by project name, with `on_project_stop` hook support.

**tmuxp equivalent**: None. Must use `tmux kill-session` or libtmux directly.

#### 15. Freeze from session (`tmuxinator new name session`)

Create config from an existing running tmux session.

**tmuxp equivalent**: `tmuxp freeze` — similar functionality, different UX.

---

## Import Gaps (tmuxinator → tmuxp)

### Currently handled by `import_tmuxinator` (`src/tmuxp/workspace/importers.py:8-102`)

| tmuxinator key | tmuxp mapping | Status |
|---|---|---|
| `project_name` / `name` | `session_name` | ✓ |
| `project_root` / `root` | `start_directory` | ✓ |
| `cli_args` / `tmux_options` | `config` (extracts `-f`) | ✓ (partial) |
| `socket_name` | `socket_name` | ✓ (but dead data — see §A.6) |
| `pre` | `shell_command_before` | ✓ |
| `pre_window` | `shell_command_before` | ✓ |
| `rbenv` | `shell_command_before` + `rbenv shell X` | ✓ |
| `tabs` | `windows` | ✓ |
| window `pre` | `shell_command_before` | ✓ |
| window `root` | `start_directory` | ✓ |
| window `layout` | `layout` | ✓ |
| window `panes` | `panes` | ✓ |

### Missing from importer

| tmuxinator key | Recommended tmuxp mapping | Notes |
|---|---|---|
| `rvm` | `shell_command_before` + `rvm use X` | Only `rbenv` is handled |
| `post` | — | No equivalent, should warn |
| `on_project_start/first_start/restart/exit/stop` | — | No equivalent without plugins, should warn |
| `startup_window` | Find matching window → `focus: true` | Translatable |
| `startup_pane` | Set `focus: true` on pane at index | Translatable |
| `attach: false` | Pass through or new config key | Translatable if config key added |
| `socket_path` | New config key needed | tmuxp has `-S` CLI but no config key |
| `tmux_command` | — | No equivalent, should warn |
| `tmux_options` (non `-f` flags) | — | Only `-f` extracted currently |
| `synchronize` | `options_after: {synchronize-panes: on}` | Translatable |
| `enable_pane_titles` / format / position | — | No equivalent |
| Named panes (hash key syntax) | Extract title, create pane with commands | Partially translatable (commands yes, title no) |
| `window_name: null` | Unnamed window handling | Should pass through as `None` |
| Window shorthand (`- name: cmd`) as string | Handle string value for window | Currently works for strings at line 83 |

### Code quality issues in current importer

1. **Mutating input**: Uses `dict.pop()` throughout, which destructively modifies the input dict. If the caller reuses the dict, data is lost.

2. **Loop variable reassignment**: At line 80-81, iterates `window_dict.items()` then immediately reassigns `window_dict = {"window_name": k}`, discarding the original reference. Only works because tmuxinator windows are single-key hashes.

3. **Minimal test coverage**: Only 3 test fixtures (`tests/fixtures/import_tmuxinator/test1-3.yaml`). No tests for hooks, `synchronize`, pane titles, `startup_window`, `attach`, named panes, or edge cases.

---

## WorkspaceBuilder Requirements for Full Tmuxinator Parity

### 1. Pane synchronization config key

Add `synchronize` as a first-class key on windows. After all panes are created:
- `synchronize: true` or `synchronize: after` → `options_after: {synchronize-panes: on}`
- `synchronize: before` → `options: {synchronize-panes: on}`

Could be sugar that maps to `options`/`options_after` during `loader.expand()`.

**Files**: `src/tmuxp/workspace/builder.py`, `src/tmuxp/workspace/loader.py`

### 2. Pane titles

New config keys:
- `enable_pane_titles: true` at session level
- `pane_title_position: top|bottom|off` at session level
- `pane_title_format: "..."` at session level
- Per-pane `title` key

**Files**: `src/tmuxp/workspace/builder.py`

### 3. Shell command hooks in config

Support hooks as shell commands in YAML (not just plugin API):
- `on_session_start` (or similar naming)
- `on_session_exit`

Different from plugin hooks which require Python packages.

**Files**: `src/tmuxp/workspace/builder.py`

### 4. `attach` config key

`attach: false` in config to prevent auto-attach, equivalent to CLI `-d`.

**Files**: `src/tmuxp/cli/load.py` (read from config, merge with CLI flag)

### 5. Socket name/path as config keys

tmuxp already has `-S`/`-L` CLI flags but NOT as workspace config keys. The `socket_name` key is mapped by the importer but never read by `load_workspace()` — it's dead data.

**Fix**: In `load_workspace()`, read `socket_name`/`socket_path` from the expanded config dict and merge with CLI args (CLI should override config).

**Files**: `src/tmuxp/cli/load.py` (lines 369-374), `src/tmuxp/workspace/builder.py`

### 6. Auto-detect config format

Add `detect_format(config_dict) -> "tmuxp" | "tmuxinator" | "teamocil"` for transparent loading of foreign configs.

**Detection heuristics**:
- **tmuxinator**: Has `project_name`/`name` + `root`/`project_root`, or `tabs`, or `pre_window`, or `on_project_*` hooks
- **teamocil**: Has `session.windows` wrapper, or `windows[].splits`, or `windows[].panes[].commands`
- **tmuxp**: Has `session_name` + `windows[].window_name`

**Files**: `src/tmuxp/workspace/importers.py` or new `src/tmuxp/workspace/detect.py`
