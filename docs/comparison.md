(comparison)=

# Comparison

*tmuxp vs tmuxinator vs teamocil*

Comparison of tmux session managers as of:

- **tmuxp** — current (`master`)
- **tmuxinator** — v3.3.7
- **teamocil** — v1.4.2

## Overview

| | tmuxp | tmuxinator | teamocil |
|---|---|---|---|
| Language | Python | Ruby | Ruby |
| Min tmux | 3.2+ | 1.8+ | 1.8+ |
| Config format | YAML, JSON | YAML (ERB) | YAML |
| Architecture | Python ORM (libtmux) | Shell script generation (ERB template) | Command objects |
| Plugin system | Yes (Python classes) | No | No |
| License | MIT | MIT | MIT |

## Configuration Keys

| Feature | tmuxp | tmuxinator | teamocil |
|---|---|---|---|
| **Session** | | | |
| Session name | `session_name` | `name` / `project_name` | `name` |
| Root directory | `start_directory` | `root` / `project_root` | — (window-level only) |
| Environment vars | `environment` (session/window/pane) | — (ERB only) | — |
| Session options | `options` | — | — |
| Global options | `global_options` | — | — |
| **Windows** | | | |
| Windows list | `windows` | `windows` / `tabs` | `windows` |
| Window name | `window_name` | hash key | `name` |
| Window root | `start_directory` | `root` | `root` |
| Layout | `layout` | `layout` | `layout` |
| Window options | `options` | — | `options` |
| Window options (post-build) | `options_after` | — | — |
| Window index | `window_index` | — | — |
| Window shell | `window_shell` | — | — |
| Window focus | `focus: true` | `startup_window` (name/index) | `focus: true` |
| **Panes** | | | |
| Panes list | `panes` | `panes` | `panes` / `splits` (v0.x) |
| Pane commands | `shell_command` | string / array / hash | `commands` / string |
| Pane focus | `focus: true` | — | `focus: true` |
| Pane shell | `shell` | — | — |
| Named panes | — | hash key = pane title | — |
| Pane sync | — | `synchronize` (`before`/`after`/`true`) | — |
| Pane titles | — | `enable_pane_titles` + format + position | — |
| **Pre/Post Commands** | | | |
| Session-level pre | `shell_command_before` | `pre` | — |
| Window-level pre | `shell_command_before` | `pre` (window) / `pre_window` | `filters.before` (v0.x) |
| Before script | `before_script` | — | — |
| **Hooks** | | | |
| Hook system | Plugin API (Python) | Config keys (shell commands) | — |
| On session start | `before_workspace_builder` (plugin) | `on_project_start` | — |
| On first start | — | `on_project_first_start` | — |
| On restart | — | `on_project_restart` | — |
| On exit | — | `on_project_exit` | — |
| On stop | — | `on_project_stop` | — |
| **Timing** | | | |
| Suppress history | `suppress_history` | — | — |
| Enter after command | `enter` | — | — |
| Sleep before/after | `sleep_before` / `sleep_after` | — | — |
| **Connection** | | | |
| Socket name | `-L` CLI flag | `socket_name` config key | — |
| Socket path | `-S` CLI flag | `socket_path` config key | — |
| tmux config file | `-f` CLI flag | `tmux_options` / `cli_args` | — |
| tmux command override | — | `tmux_command` (wemux/byobu) | — |
| Attach control | `-d` CLI flag only | `attach: false` config key | — |
| **Startup Selection** | | | |
| Startup window | `focus: true` on window | `startup_window` (name/index) | `focus: true` on window |
| Startup pane | `focus: true` on pane | `startup_pane` (index) | `focus: true` on pane |
| **Templating** | | | |
| Variable expansion | `$ENV_VAR`, `~` | ERB (`<%= %>`) with args/settings | — |
| Config arguments | — | `tmuxinator start proj arg1 k=v` | — |
| **Misc** | | | |
| Append mode | `--append` / `-a` CLI | `--append` CLI (v3.3+) | `--here` CLI |
| Custom layout strings | Yes | Yes | Yes |
| YAML anchors | Yes | Yes | Yes |
| JSON config support | Yes | — | — |
| Wemux/byobu support | — | Yes (`tmux_command`) | — |
| rbenv/rvm shortcuts | — (use `shell_command_before`) | `rbenv` / `rvm` (deprecated) | — |

## CLI Commands

| Action | tmuxp | tmuxinator | teamocil |
|---|---|---|---|
| Load session | `tmuxp load <config>` | `tmuxinator start <project>` | `teamocil <layout>` |
| Load detached | `tmuxp load -d <config>` | `tmuxinator start -d` / `attach: false` | — |
| Append to session | `tmuxp load -a <config>` | `tmuxinator start --append` | `teamocil --here` |
| Freeze/export session | `tmuxp freeze <session>` | `tmuxinator new <name> <session>` | — |
| Convert format | `tmuxp convert <file>` | — | — |
| Import config | `tmuxp import <format> <file>` | — | — |
| Edit config | `tmuxp edit <config>` | `tmuxinator edit <project>` | `teamocil --edit <layout>` |
| List configs | `tmuxp ls` | `tmuxinator list` | `teamocil --list` |
| Search configs | `tmuxp search <query>` | — | — |
| Copy config | — | `tmuxinator copy <src> <dst>` | — |
| Debug/dry-run | — | `tmuxinator debug <project>` | `teamocil --debug` |
| Show config | — | — | `teamocil --show <layout>` |
| Debug info | `tmuxp debug-info` | `tmuxinator doctor` | — |
| Shell | `tmuxp shell` | — | — |
| Stop session | — | `tmuxinator stop <project>` | — |
| Stop all sessions | — | `tmuxinator stop --all` | — |
| Delete config | — | `tmuxinator delete <project>` | — |
| Completions | `tmuxp --print-completion` | `tmuxinator completions` | — |

## Architecture Comparison

### tmuxp — Python ORM

tmuxp uses [libtmux](https://github.com/tmux-python/libtmux) to interact with tmux through Python objects. `Server`, `Session`, `Window`, and `Pane` are first-class Python objects with methods that execute tmux commands and parse their output.

**WorkspaceBuilder** reads the config dict and calls libtmux methods to create sessions, windows, and panes. This gives tmuxp full programmatic control over tmux objects, enabling features like the plugin system, `tmuxp shell`, and `tmuxp freeze`.

**Strengths**: Rich Python API, plugin extensibility, type safety, programmatic access to tmux state.

**Trade-offs**: Tightly coupled to `tmux` binary (can't swap for wemux/byobu easily), requires Python runtime.

### tmuxinator — Shell Script Generation

tmuxinator uses an ERB template (`template.erb`) to generate a bash script that contains raw tmux commands. The generated script is then executed by the shell.

**Strengths**: ERB templating with arguments, wemux/byobu support (just change the binary name), shell hooks are natural (they're part of the script), debug mode shows the generated script.

**Trade-offs**: No programmatic access to tmux state, limited error handling, shell escaping challenges.

### teamocil — Command Objects

teamocil builds an array of command objects (`Tmux::Session`, `Tmux::Window`, `Tmux::Pane`) that each know how to generate their tmux commands. Commands are collected and executed sequentially.

**Strengths**: Clean separation between command generation and execution, simple codebase, debug mode.

**Trade-offs**: Minimal feature set, no hooks, no templating, no session export.
