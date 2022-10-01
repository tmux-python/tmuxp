(api)=

# API Reference

:::{seealso}
See {ref}`libtmux's API <libtmux:api>` and {ref}`Quickstart <libtmux:quickstart>` to see how you can control
tmux via python API calls.
:::

## Internals

:::{warning}
Be careful with these! Internal APIs are **not** covered by version policies. They can break or be removed between minor versions.

If you need an internal API stabilized please [file an issue](https://github.com/tmux-python/tmuxp/issues).
:::

```{eval-rst}
.. automethod:: tmuxp.util.run_before_script
```

```{eval-rst}
.. automethod:: tmuxp.util.oh_my_zsh_auto_title
```

```{eval-rst}
.. automethod:: tmuxp.util.raise_if_tmux_not_running
```

```{eval-rst}
.. automethod:: tmuxp.util.get_current_pane
```

```{eval-rst}
.. automethod:: tmuxp.util.get_session
```

```{eval-rst}
.. automethod:: tmuxp.util.get_window
```

```{eval-rst}
.. automethod:: tmuxp.util.get_pane
```

## CLI

```{eval-rst}
.. automethod:: tmuxp.cli.utils.get_config_dir
```

```{eval-rst}
.. automethod:: tmuxp.cli.utils._validate_choices
```

```{eval-rst}
.. automethod:: tmuxp.cli.import_config.get_teamocil_dir
```

```{eval-rst}
.. automethod:: tmuxp.cli.import_config.get_tmuxinator_dir
```

```{eval-rst}
.. automethod:: tmuxp.cli.load.load_workspace
```

```{eval-rst}
.. automethod:: tmuxp.cli.load._reattach
```

## Configuration

### Finding

```{eval-rst}
.. automethod:: tmuxp.config.is_config_file
```

```{eval-rst}
.. automethod:: tmuxp.config.in_dir
```

```{eval-rst}
.. automethod:: tmuxp.config.in_cwd
```

### Import and export

```{eval-rst}
.. automethod:: tmuxp.config.validate_schema
```

```{eval-rst}
.. automethod:: tmuxp.config.expandshell
```

```{eval-rst}
.. automethod:: tmuxp.config.expand
```

```{eval-rst}
.. automethod:: tmuxp.config.inline
```

```{eval-rst}
.. automethod:: tmuxp.config.trickle
```

```{eval-rst}
.. automethod:: tmuxp.config.import_teamocil
```

```{eval-rst}
.. automethod:: tmuxp.config.import_tmuxinator
```

## Configuration reader

```{eval-rst}
.. automodule:: tmuxp.config_reader
```

## Workspace Builder

```{eval-rst}
.. autoclass:: tmuxp.workspacebuilder.WorkspaceBuilder
   :members:
```

```{eval-rst}
.. automethod:: tmuxp.workspacebuilder.freeze
```

## Exceptions

```{eval-rst}
.. autoexception:: tmuxp.exc.EmptyConfigException
```

```{eval-rst}
.. autoexception:: tmuxp.exc.ConfigError
```

```{eval-rst}
.. autoexception:: tmuxp.exc.BeforeLoadScriptError
```

```{eval-rst}
.. autoexception:: tmuxp.exc.BeforeLoadScriptNotExists
```
