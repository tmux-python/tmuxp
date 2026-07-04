# Chain builder - `tmuxp.workspace.builder.chain`

:::{warning}
The chain builder is **experimental** and depends on libtmux's unreleased chain
API (libtmux#685). That API is absent from published libtmux builds, so
selecting `workspace_builder: chain` raises
{exc}`~tmuxp.exc.WorkspaceBuilderImportError` until it ships. The module itself
imports cleanly without the API.
:::

```{eval-rst}
.. automodule:: tmuxp.workspace.builder.chain
   :members:
   :show-inheritance:
   :undoc-members:
```
