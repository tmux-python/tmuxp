(cli-delete)=

(cli-delete-reference)=

# tmuxp delete

Delete one or more workspace config files. Prompts for confirmation unless `-y` is passed.

## Command

```{eval-rst}
.. argparse::
    :module: tmuxp.cli
    :func: create_parser
    :prog: tmuxp
    :path: delete
```

## Basic usage

Delete a workspace:

```console
$ tmuxp delete old-project
```

Delete without confirmation:

```console
$ tmuxp delete -y old-project
```

Delete multiple workspaces:

```console
$ tmuxp delete proj1 proj2
```

```{note}
Only workspace files are deletable: the resolved path must end in `.yaml`, `.yml`, or `.json`. Any other file is refused and the command exits with code 1.
```
