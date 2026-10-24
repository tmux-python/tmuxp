(cli-debug-info)=

(tmuxp-debug-info)=

# tmuxp debug-info

Collect and display system information useful for debugging tmuxp issues and
submitting bug reports. The command remains available when tmux is missing
or the selected daemon is below the minimum. It does not start a server.

JSON output keeps unavailable state lists empty and records the reason in
`tmux_errors`, keyed by the failed query. `tmux_version` describes the
executable, while version errors in `tmux_errors` describe the daemon.

## Command

```{eval-rst}
.. argparse::
    :module: tmuxp.cli
    :func: create_parser
    :prog: tmuxp
    :path: debug-info
```

## Example output

```console

$ tmuxp debug-info
--------------------------
environment:
    system: Linux
    arch: x86_64
...

```
