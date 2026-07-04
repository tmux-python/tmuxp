(cli-stop)=

(cli-stop-reference)=

# tmuxp stop

Stop (kill) a running tmux session. If `on_project_stop` is defined in the workspace config, that hook runs before the session is killed.

## Command

```{eval-rst}
.. argparse::
    :module: tmuxp.cli
    :func: create_parser
    :prog: tmuxp
    :path: stop
```

## Basic usage

Stop a session by name:

```console
$ tmuxp stop mysession
```

Stop the currently attached session:

```console
$ tmuxp stop
```

Use a custom socket:

```console
$ tmuxp stop -L mysocket mysession
```
