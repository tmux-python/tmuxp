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

## Workspace files

### Finding

```{eval-rst}
.. automethod:: tmuxp.workspace.finders.is_workspace_file
```

```{eval-rst}
.. automethod:: tmuxp.workspace.finders.in_dir
```

```{eval-rst}
.. automethod:: tmuxp.workspace.finders.in_cwd
```

```{eval-rst}
.. automethod:: tmuxp.workspace.finders.get_workspace_dir
```

### Validation

```{eval-rst}
.. autofunction:: tmuxp.workspace.validation.validate_schema
```

### Processing

```{eval-rst}
.. automethod:: tmuxp.workspace.loader.expandshell
```

```{eval-rst}
.. automethod:: tmuxp.workspace.loader.expand
```

```{eval-rst}
.. automethod:: tmuxp.workspace.loader.trickle
```

## Workspace importers

```{eval-rst}
.. automethod:: tmuxp.workspace.importers.import_teamocil
```

```{eval-rst}
.. automethod:: tmuxp.workspace.importers.import_tmuxinator
```

## Configuration reader

```{eval-rst}
.. automodule:: tmuxp.config_reader
```

## Workspace Builder

```{eval-rst}
.. autoclass:: tmuxp.workspace.builder.WorkspaceBuilder
   :members:
```

## Workspace Freezer

```{eval-rst}
.. automethod:: tmuxp.workspace.freezer.freeze
```

```{eval-rst}
.. automethod:: tmuxp.workspace.freezer.inline
```

## Exceptions

```{eval-rst}
.. autoexception:: tmuxp.exc.EmptyWorkspaceException
```

```{eval-rst}
.. autoexception:: tmuxp.exc.WorkspaceError
```

```{eval-rst}
.. autoexception:: tmuxp.exc.BeforeLoadScriptError
```

```{eval-rst}
.. autoexception:: tmuxp.exc.BeforeLoadScriptNotExists
```
