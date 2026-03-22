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

### Importer improvements

The teamocil importer now supports:

- **v1.x format** — `windows` at top level with `commands` key in panes
- **Focus** — `focus: true` on windows and panes is preserved
- **Window options** — `options` on windows are passed through

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

### Importer improvements

The tmuxinator importer now supports:

- **Hook mapping** — `pre` maps to `before_script`, `pre_window` maps to `shell_command_before`
- **CLI args** — `cli_args` values (`-f`, `-S`, `-L`) are parsed into tmuxp config equivalents
- **Synchronize** — `synchronize` window key is converted
- **Startup focus** — `startup_window` / `startup_pane` convert to `focus: true`
- **Named panes** — hash-key pane syntax converts to `title` on the pane
