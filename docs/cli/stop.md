(cli-stop)=

(cli-stop-reference)=

# tmuxp stop

Stop (kill) a running tmux session. If the session was created from a workspace
with `on_project_stop`, that hook runs before the session is killed.

## Command

```{eval-rst}
.. argparse::
    :module: tmuxp.cli
    :func: create_parser
    :prog: tmuxp
    :path: stop
```

## Basic Usage

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
