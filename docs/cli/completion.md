(completion)=

(completions)=

(cli-completions)=

# Completions

## tmuxp 1.17+ (experimental)

```{note}
See the [shtab library's documentation on shell completion](https://docs.iterative.ai/shtab/use/#cli-usage) for the most up to date way of connecting completion for tmuxp.
```

Provisional support for completions in tmuxp 1.17+ are powered by [shtab](https://docs.iterative.ai/shtab/). This must be **installed separately**, as it's **not currently bundled with tmuxp**.

```console
$ pip install shtab --user
```

With a [uv](https://docs.astral.sh/uv/getting-started/features/#python-versions) project you can add it directly as a development dependency:

```console
$ uv add --dev shtab
```

Or reach for [uvx](https://docs.astral.sh/uv/guides/tools/) when you want a pipx-style ephemeral install:

```console
$ uvx shtab --help
```

:::{tab} bash

```bash
shtab --shell=bash -u tmuxp.cli.create_parser \
  | sudo tee "$BASH_COMPLETION_COMPAT_DIR"/TMUXP
```

:::

:::{tab} zsh

```zsh
shtab --shell=zsh -u tmuxp.cli.create_parser \
  | sudo tee /usr/local/share/zsh/site-functions/_TMUXP
```

:::

:::{tab} tcsh

```zsh
shtab --shell=tcsh -u tmuxp.cli.create_parser \
  | sudo tee /etc/profile.d/TMUXP.completion.csh
```

:::

## tmuxp 1.1 to 1.16

```{note}
See the [click library's documentation on shell completion](https://click.palletsprojects.com/en/8.0.x/shell-completion/) for the most up to date way of connecting completion for tmuxp.
```

tmuxp 1.1 to 1.16 use [click](https://click.palletsprojects.com)'s completion:

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
