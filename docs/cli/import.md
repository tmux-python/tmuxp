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

### Supported teamocil fields

The teamocil importer preserves top-level and `session`-wrapped configs, window
`root`, `layout`, `clear`, `focus`, `options`, and `filters` entries. Pane
entries using `cmd`, `commands`, string panes, and blank panes are converted to
tmuxp pane dictionaries. Unsupported pane `width` and `height` values are
dropped with a warning.

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

### Supported tmuxinator fields

The tmuxinator importer maps `project_name`/`name`, `project_root`/`root`,
legacy `tabs`, `cli_args`/`tmux_options` values for `-f`, `-L`, and `-S`,
`socket_name`, `socket_path`, `pre`, `pre_window`, `pre_tab`, `rbenv`, `rvm`,
`startup_window`, `startup_pane`, `synchronize`, pane-title keys, and lifecycle
hook keys.

Named pane entries such as `{logs: tail -f log/development.log}` become tmuxp
pane `title` values. Imported `config` values are resolved relative to the saved
workspace file when the workspace is loaded.

````{tab} JSON

```console
$ tmuxp import tmuxinator /path/to/file.json
```

````
