(cli-convert)=

# tmuxp convert

Convert workspace configuration files between YAML and JSON formats.

## Command

```{eval-rst}
.. argparse::
    :module: tmuxp.cli
    :func: create_parser
    :prog: tmuxp
    :path: convert
```

## Basic usage

````{tab} YAML -> JSON

```console
$ tmuxp convert /path/to/file.yaml
```

````

````{tab} JSON -> YAML

```console
$ tmuxp convert /path/to/file.json
```

````

tmuxp automatically will prompt to convert `.yaml` to `.json` and
`.json` to `.yaml`.
