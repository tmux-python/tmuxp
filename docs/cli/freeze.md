(cli-freeze)=

# tmuxp freeze

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

If the `--force` argument is passed, it will overwrite any existing config file with the same name.

(cli-freeze-reference)=

```{eval-rst}
.. click:: tmuxp.cli.freeze:command_freeze
    :prog: tmuxp freeze
    :commands: freeze
    :nested: full
```
