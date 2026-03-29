(cli-new)=

(cli-new-reference)=

# tmuxp new

Create a new workspace configuration file from a minimal template and open it in `$EDITOR`. If the workspace already exists, it opens for editing.

## Command

```{eval-rst}
.. argparse::
    :module: tmuxp.cli
    :func: create_parser
    :prog: tmuxp
    :path: new
```

## Basic usage

Create a new workspace:

```console
$ tmuxp new myproject
```
