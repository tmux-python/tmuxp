# Builder - `tmuxp.workspace.builder`

`tmuxp.workspace.builder` is a package. The classic, default builder lives in
{mod}`tmuxp.workspace.builder.classic`; the public contract and the selection
machinery live alongside it.

`WorkspaceBuilder` remains importable from `tmuxp.workspace.builder` as a
backwards-compatible alias of
{class}`~tmuxp.workspace.builder.classic.ClassicWorkspaceBuilder`.

::::{grid} 1 1 2 2
:gutter: 2 2 3 3

:::{grid-item-card} Classic builder
:link: classic
:link-type: doc
The built-in, default builder — `tmuxp.workspace.builder.classic`.
:::

:::{grid-item-card} Builder protocol
:link: protocol
:link-type: doc
The contract a builder must satisfy — `tmuxp.workspace.builder.protocol`.
:::

:::{grid-item-card} Builder registry
:link: registry
:link-type: doc
Builder selection and trusted import paths — `tmuxp.workspace.builder.registry`.
:::

::::

```{toctree}
:hidden:

classic
protocol
registry
```
