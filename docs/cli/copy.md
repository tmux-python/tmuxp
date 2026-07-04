(cli-copy)=

(cli-copy-reference)=

# tmuxp copy

Copy an existing workspace config to a new name. Source is resolved using the same logic as `tmuxp load` (supports names, paths, and extensions).

## Command

```{eval-rst}
.. argparse::
    :module: tmuxp.cli
    :func: create_parser
    :prog: tmuxp
    :path: copy
```

## Basic usage

Copy a workspace:

```console
$ tmuxp copy myproject myproject-backup
```
