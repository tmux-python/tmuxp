(completion)=

# Completion

```{note}
See the [click library's documentation on shell completion](https://click.palletsprojects.com/en/8.0.x/shell-completion/) for the most up to date way of connecting completion for vcspull.
```

:::{tab} Bash

_~/.bashrc_:

```bash

eval "$(_TMUXP_COMPLETE=bash_source tmuxp)"

```

:::

:::{tab} Zsh

_~/.zshrc_:

```zsh

eval "$(_TMUXP_COMPLETE=zsh_source tmuxp)"

```

:::
