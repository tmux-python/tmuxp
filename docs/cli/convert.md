(cli-convert)=

# tmuxp convert

```{eval-rst}
.. argparse::
    :module: tmuxp.cli
    :func: create_parser
    :prog: tmuxp
    :path: convert
```

## Usage

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
