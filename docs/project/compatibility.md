# tmux compatibility

tmuxp requires tmux 3.3a or newer. The patch letter matters: tmux 3.3 is below
the minimum. Ordinary workspace creation, pane splitting, input, capture,
layout, and freezing remain available on tmux 3.3a.

The selected daemon determines compatibility when a socket is already
running. A cold socket uses the selected executable's version. Installing a
new executable does not upgrade an existing daemon. Save your sessions
before restarting an older daemon, or use a new socket name.

Workspace loading checks the selected endpoint before importing a custom
builder or plugin. The classic builder checks a supplied session or window's
server before callbacks and scripts. `tmuxp shell` checks before executing
`-c`, importing a shell, or loading `PYTHONSTARTUP`. Later native operations
carry libtmux's command version check. They refuse a replacement daemon whose
version differs from the version checked for that command.

`--help`, `--version`, `debug-info`, and workspace conversion remain available
without a running server or an installed tmux executable.

## Optional operations

Plugins, custom builders, and `tmuxp shell` receive libtmux objects. Their
optional operations have individual tmux requirements:

| Operation | Requirement |
| --- | --- |
| Acquire a control-mode client | Stable tmux 3.7+ and a natively compatible client |
| Preserve exact named-buffer identity when deleting, renaming, or aborting cleanup | tmux 3.4+ |
| Return foreground `run-shell` stdout | tmux 3.5+ |
| Break a pane on exact tmux 3.7 | Supply a window name; the wrapper repairs the native name handling. Unnamed and raw calls refuse. |
| Split by percentage | Available on tmux 3.3a+ through the portable `-l N%` spelling |
| Select a literal layout on tmux 3.3a | Use a unique built-in layout name or a serialized layout. Malformed headers refuse before the native 3.3a error path. |

An unavailable operation refuses before its native command runs. An
ordinary workspace still builds, splits, captures, and freezes on tmux
3.3a. Background shell jobs and jobs directed to a pane keep their separate
execution-only contract.

## Installing this checkout

This branch requires libtmux 0.63 or newer, the first release that carries
the daemon version check and its `require_commands` policy, and
`pyproject.toml` says so (`libtmux~=0.63.0`). Until that release exists,
`uv.lock` pins an exact development revision. Install the checkout with its
lockfile:

```console
$ uv sync --locked
```

A plain package install does not apply uv's source selection and picks the
released libtmux. If the installed libtmux lacks the version check, tmuxp
refuses to load, freeze, or open a shell. Release libtmux first, then drop the
source pin and merge this change.

## Workspace scripts and custom code

tmuxp sends `shell_command` text to a pane's shell. That shell executes the
operator's code. `before_script` runs a separate program, and plugins and
custom builders execute Python code. The compatibility check does not parse
or constrain those programs, their own tmux clients, or commands embedded
inside scripts. Redefining libtmux's built-in tmux commands through
`command-alias` also falls outside the managed command guarantee.

Readiness polling and configured `sleep_before`/`sleep_after` values remain
part of workspace behavior. Raising the minimum does not make shell startup
or asynchronous terminal output immediate.
