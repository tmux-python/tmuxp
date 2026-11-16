(cli-ls)=

(ls-config)=

# tmuxp ls

List available workspace configurations from your local project and global tmuxp directories.

```{image} ../_static/demos/asciinema/tmuxp-ls.gif
:alt: tmuxp ls listing configured workspaces
:width: 100%
:loading: lazy
```

## Command

```{eval-rst}
.. argparse::
    :module: tmuxp.cli
    :func: create_parser
    :prog: tmuxp
    :path: ls
```
