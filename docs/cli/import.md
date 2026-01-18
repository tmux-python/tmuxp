(cli-import)=

# tmuxp import

Import and convert workspace configurations from other tmux session managers like teamocil and tmuxinator.

(import-teamocil)=

## From teamocil

Import teamocil configuration files and convert them to tmuxp format.

### Command

```{eval-rst}
.. argparse::
    :module: tmuxp.cli
    :func: create_parser
    :prog: tmuxp
    :path: import teamocil
```

### Basic usage

````{tab} YAML

```console
$ tmuxp import teamocil /path/to/file.yaml
```

````

````{tab} JSON

```console
$ tmuxp import teamocil /path/to/file.json
```

````

(import-tmuxinator)=

## From tmuxinator

Import tmuxinator configuration files and convert them to tmuxp format.

### Command

```{eval-rst}
.. argparse::
    :module: tmuxp.cli
    :func: create_parser
    :prog: tmuxp
    :path: import tmuxinator
```

### Basic usage

````{tab} YAML

```console
$ tmuxp import tmuxinator /path/to/file.yaml
```

````

````{tab} JSON

```console
$ tmuxp import tmuxinator /path/to/file.json
```

````
