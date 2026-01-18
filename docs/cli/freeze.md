(cli-freeze)=

(cli-freeze-reference)=

# tmuxp freeze

Export a running tmux session to a workspace configuration file. This allows you to save the current state of your tmux session for later restoration.

## Command

```{eval-rst}
.. argparse::
    :module: tmuxp.cli
    :func: create_parser
    :prog: tmuxp
    :path: freeze
```

## Basic usage

Freeze the current session:

```console
$ tmuxp freeze
```

Freeze a specific session by name:

```console
$ tmuxp freeze [session_name]
```

Overwrite an existing workspace file:

```console
$ tmuxp freeze --force [session_name]
```

## Output format

Tmuxp will offer to save your session state to `.json` or `.yaml`.

If no session is specified, it will default to the attached session.

If the `--force` argument is passed, it will overwrite any existing workspace file with the same name.
