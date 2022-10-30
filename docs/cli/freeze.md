(cli-freeze)=

(cli-freeze-reference)=

# tmuxp freeze

```{eval-rst}
.. argparse::
    :module: tmuxp.cli
    :func: create_parser
    :prog: tmuxp
    :path: freeze
```

## Usage

Freeze sessions

```console
$ tmuxp freeze
```

```console
$ tmuxp freeze [session_name]
```

```console
$ tmuxp freeze --force [session_name]
```

You can save the state of your tmux session by freezing it.

Tmuxp will offer to save your session state to `.json` or `.yaml`.

If no session is specified, it will default to the attached session.

If the `--force` argument is passed, it will overwrite any existing workspace file with the same name.
