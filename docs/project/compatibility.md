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

## Installing this checkout

This branch depends on coordinated, unreleased libtmux admission changes.
`uv.lock` pins their exact source revision; the package version by itself
does not identify those changes. Install the checkout with its lockfile:

```console
$ uv sync --locked
```

A plain package install does not apply uv's source selection. The installed
libtmux must provide the coordinated admission API before tmuxp can load,
freeze, or open a shell. The matching release pair must be published before
this branch can serve as a normal registry release.

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
