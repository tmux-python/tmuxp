(cli-search)=

(search-config)=

# tmuxp search

Search for workspace configurations by name or content across your tmuxp directories.

```{image} ../_static/demos/asciinema/tmuxp-search.gif
:alt: tmuxp search narrowing workspaces to those with an editor window
:width: 100%
:loading: lazy
```

## Command

```{eval-rst}
.. argparse::
    :module: tmuxp.cli
    :func: create_parser
    :prog: tmuxp
    :path: search
```
