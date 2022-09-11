(cli-convert)=

# tmuxp convert

Convert between YAML and JSON

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

## Reference

```{eval-rst}
.. click:: tmuxp.cli.convert:command_convert
    :prog: tmuxp convert
    :commands: convert
    :nested: full
```
