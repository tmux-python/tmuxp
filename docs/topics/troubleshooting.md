# Troubleshooting

## tmuxp command not found

Ensure tmuxp is installed and on your `PATH`:

```console
$ which tmuxp
```

If installed with `pip install --user`, ensure `~/.local/bin` is in your `PATH`.

## tmux server not found

tmuxp requires a running tmux server or will start one automatically.
Ensure tmux is installed:

```console
$ tmux -V
```

Minimum required version: tmux 3.2.

## Configuration errors

Use {ref}`tmuxp debug-info <cli-debug-info>` to collect system information for
bug reports:

```console
$ tmuxp debug-info
```

## Session already exists

If a session with the same name already exists, tmuxp will prompt you.
Use {ref}`tmuxp load -d <cli-load>` to load in detached mode alongside existing
sessions.

## Shell completion not working

See {ref}`completion` for setup instructions for bash, zsh, and tcsh.
