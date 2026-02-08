# Feature Comparison: tmuxp vs tmuxinator vs teamocil

*Last updated: 2026-02-08*

## Overview

| | tmuxp | tmuxinator | teamocil |
|---|---|---|---|
| **Version** | 1.47.0+ | 3.3.7 | 1.4.2 |
| **Language** | Python | Ruby | Ruby |
| **Min tmux** | 3.2 | 1.8 (recommended; not 2.5) | (not specified) |
| **Config formats** | YAML, JSON | YAML (with ERB) | YAML |
| **Architecture** | ORM (libtmux) | Script generation (ERB templates) | Command objects → shell exec |
| **License** | MIT | MIT | MIT |
| **Session building** | API calls via libtmux | Generates bash script, then execs it | Generates tmux command string, then `system()` |
| **Plugin system** | Yes (Python classes) | No | No |
| **Shell completion** | Yes | Yes (zsh/bash/fish) | No |

## Architecture Comparison

### tmuxp — ORM-Based

tmuxp uses **libtmux**, an object-relational mapper for tmux. Each tmux entity (server, session, window, pane) has a Python object with methods that issue tmux commands via `tmux(1)`. Configuration is parsed into Python dicts, then the `WorkspaceBuilder` iterates through them, calling libtmux methods.

**Advantages**: Programmatic control, error recovery mid-build, plugin hooks at each lifecycle stage, Python API for scripting.

**Disadvantages**: Requires Python runtime, tightly coupled to libtmux API.

### tmuxinator — Script Generation

tmuxinator reads YAML (with ERB templating), builds a `Project` object graph, then renders a bash script via ERB templates. The generated script is `exec`'d, replacing the tmuxinator process.

**Advantages**: Debuggable output (`tmuxinator debug`), wide tmux version support (1.8+), ERB allows config templating with variables.

**Disadvantages**: No mid-build error recovery (script runs or fails), Ruby dependency.

### teamocil — Command Objects

teamocil parses YAML into `Session`/`Window`/`Pane` objects, each producing `Command` objects with `to_s()` methods. Commands are joined with `; ` and executed via `Kernel.system()`.

**Advantages**: Simple, predictable, debuggable (`--debug`).

**Disadvantages**: No error recovery, no hooks, no templating, minimal feature set.

## Configuration Keys

### Session-Level

| Key | tmuxp | tmuxinator | teamocil |
|---|---|---|---|
| Session name | `session_name` | `name` / `project_name` | `name` |
| Root directory | `start_directory` | `root` / `project_root` | (none, per-window only) |
| Windows list | `windows` | `windows` / `tabs` | `windows` |
| Socket name | (CLI `-L`) | `socket_name` | (none) |
| Socket path | (CLI `-S`) | `socket_path` | (none) |
| Attach on create | (CLI `-d` to detach) | `attach` (default: true) | (always attaches) |
| Tmux config file | (CLI `-f`) | `tmux_options` / `cli_args` | (none) |
| Tmux command | (none) | `tmux_command` (e.g. `wemux`) | (none) |
| Session options | `options` | (none) | (none) |
| Global options | `global_options` | (none) | (none) |
| Environment vars | `environment` | (none) | (none) |
| Pre-build script | `before_script` | (none) | (none) |
| Shell cmd before (all panes) | `shell_command_before` | `pre_window` / `pre_tab` (deprecated) | (none) |
| Startup window | (none) | `startup_window` (name or index) | (none) |
| Startup pane | (none) | `startup_pane` | (none) |
| Plugins | `plugins` | (none) | (none) |
| ERB/variable interpolation | (none) | Yes (`key=value` args) | (none) |
| YAML anchors | Yes | Yes (via `YAML.safe_load` `aliases: true`) | Yes |
| Pane titles enable | (none) | `enable_pane_titles` | (none) |
| Pane title position | (none) | `pane_title_position` | (none) |
| Pane title format | (none) | `pane_title_format` | (none) |

### Session Hooks

| Hook | tmuxp | tmuxinator | teamocil |
|---|---|---|---|
| Before session build | `before_script` | `on_project_start` | (none) |
| First start only | (none) | `on_project_first_start` | (none) |
| On reattach | Plugin: `reattach()` | `on_project_restart` | (none) |
| On exit/detach | (none) | `on_project_exit` | (none) |
| On stop/kill | (none) | `on_project_stop` | (none) |
| Before workspace build | Plugin: `before_workspace_builder()` | (none) | (none) |
| On window create | Plugin: `on_window_create()` | (none) | (none) |
| After window done | Plugin: `after_window_finished()` | (none) | (none) |
| Deprecated pre/post | (none) | `pre` / `post` | (none) |

### Window-Level

| Key | tmuxp | tmuxinator | teamocil |
|---|---|---|---|
| Window name | `window_name` | hash key | `name` |
| Window index | `window_index` | (auto, sequential) | (auto, sequential) |
| Root directory | `start_directory` | `root` (relative to project root) | `root` |
| Layout | `layout` | `layout` | `layout` |
| Panes list | `panes` | `panes` | `panes` |
| Window options | `options` | (none) | `options` |
| Post-create options | `options_after` | (none) | (none) |
| Shell cmd before | `shell_command_before` | `pre` | (none) |
| Shell for window | `window_shell` | (none) | (none) |
| Environment vars | `environment` | (none) | (none) |
| Suppress history | `suppress_history` | (none) | (none) |
| Focus | `focus` | (none) | `focus` |
| Synchronize panes | (none) | `synchronize` | (none) |
| Filters (before) | (none) | (none) | `filters.before` (v0.x) |
| Filters (after) | (none) | (none) | `filters.after` (v0.x) |

### Pane-Level

| Key | tmuxp | tmuxinator | teamocil |
|---|---|---|---|
| Commands | `shell_command` | (value: string/list) | `commands` |
| Root directory | `start_directory` | (none, inherits) | (none, inherits) |
| Shell | `shell` | (none) | (none) |
| Environment vars | `environment` | (none) | (none) |
| Press enter | `enter` | (always) | (always) |
| Sleep before | `sleep_before` | (none) | (none) |
| Sleep after | `sleep_after` | (none) | (none) |
| Suppress history | `suppress_history` | (none) | (none) |
| Focus | `focus` | (none) | `focus` |
| Pane title | (none) | hash key (named pane) | (none) |

### Shorthand Syntax

| Pattern | tmuxp | tmuxinator | teamocil |
|---|---|---|---|
| String pane | `- vim` | `- vim` | `- vim` |
| List of commands | `- [cmd1, cmd2]` | `- [cmd1, cmd2]` | `commands: [cmd1, cmd2]` |
| Empty/blank pane | `- blank` / `- pane` / `- null` | `- ` (nil) | (omit commands) |
| Named pane | (none) | `- name: cmd` | (none) |
| Window as string | (none) | `window_name: cmd` | (none) |
| Window as list | (none) | `window_name: [cmd1, cmd2]` | (none) |

## CLI Commands

| Function | tmuxp | tmuxinator | teamocil |
|---|---|---|---|
| Load/start session | `tmuxp load <config>` | `tmuxinator start <project>` | `teamocil <layout>` |
| Load detached | `tmuxp load -d <config>` | `attach: false` / `tmuxinator start --no-attach` | (none) |
| Load with name override | `tmuxp load -s <name> <config>` | `tmuxinator start -n <name>` | (none) |
| Append to session | `tmuxp load -a` | `tmuxinator start --append` | (none) |
| List configs | `tmuxp ls` | `tmuxinator list` | `teamocil --list` |
| Edit config | `tmuxp edit <config>` | `tmuxinator edit <project>` (alias of `new`) | `teamocil --edit <layout>` |
| Show/debug config | (none) | `tmuxinator debug <project>` | `teamocil --show` / `--debug` |
| Create new config | (none) | `tmuxinator new <project>` | (none) |
| Copy config | (none) | `tmuxinator copy <src> <dst>` | (none) |
| Delete config | (none) | `tmuxinator delete <project>` | (none) |
| Delete all configs | (none) | `tmuxinator implode` | (none) |
| Stop/kill session | (none) | `tmuxinator stop <project>` | (none) |
| Stop all sessions | (none) | `tmuxinator stop-all` | (none) |
| Freeze/export session | `tmuxp freeze <session>` | (none) | (none) |
| Convert format | `tmuxp convert <file>` | (none) | (none) |
| Import config | `tmuxp import <tmuxinator\|teamocil> <file>` | (none) | (none) |
| Search workspaces | `tmuxp search <pattern>` | (none) | (none) |
| Python shell | `tmuxp shell` | (none) | (none) |
| Debug/system info | `tmuxp debug-info` | `tmuxinator doctor` | (none) |
| Use here (current window) | (none) | (none) | `teamocil --here` |
| Skip pre_window | (none) | `--no-pre-window` | (none) |
| Pass variables | (none) | `key=value` args | (none) |
| Custom config path | `tmuxp load /path/to/file` | `-p /path/to/file` | `--layout /path/to/file` |
| Local config | `tmuxp load .` | `tmuxinator local` | (none) |

## Config File Discovery

| Feature | tmuxp | tmuxinator | teamocil |
|---|---|---|---|
| Global directory | `~/.tmuxp/` (legacy), `~/.config/tmuxp/` (XDG) | `~/.tmuxinator/`, `~/.config/tmuxinator/` (XDG), `$TMUXINATOR_CONFIG` | `~/.teamocil/` |
| Local config | `.tmuxp.yaml`, `.tmuxp.yml`, `.tmuxp.json` (traverses up to `~`) | `.tmuxinator.yml`, `.tmuxinator.yaml` (current dir only) | (none) |
| Env override | `$TMUXP_CONFIGDIR` | `$TMUXINATOR_CONFIG` | (none) |
| XDG support | Yes (`$XDG_CONFIG_HOME/tmuxp/`) | Yes (`$XDG_CONFIG_HOME/tmuxinator/`) | No |
| Extension search | `.yaml`, `.yml`, `.json` | `.yml`, `.yaml` | `.yml` |
| Recursive search | No | Yes (`Dir.glob("**/*.{yml,yaml}")`) | No |
| Upward traversal | Yes (cwd → `~`) | No | No |
