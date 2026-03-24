(internals)=

# Internals

```{warning}
Everything in this section is **internal implementation detail**. There is
no stability guarantee. Interfaces may change or be removed without notice
between any release.

If you are building an application with tmuxp, use the [CLI](../cli/index.md)
or refer to the [libtmux API](https://libtmux.git-pull.com/api/).
```

::::{grid} 1 1 2 2
:gutter: 2 2 3 3

:::{grid-item-card} Architecture
:link: architecture
:link-type: doc
How the CLI dispatches to the workspace builder and libtmux.
:::

:::{grid-item-card} Python API
:link: api/index
:link-type: doc
Internal module reference for contributors and plugin authors.
:::

::::

```{toctree}
:hidden:

architecture
api/index
```
