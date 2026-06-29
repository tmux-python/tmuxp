(workspace-builders)=

# Workspace builders

```{versionadded} 1.72.0
```

A *workspace builder* is the part of tmuxp that turns a workspace configuration into a
live tmux session — it creates the session, lays out its windows and panes, and runs
their commands. You usually never have to think about it: tmuxp ships with a built-in
*classic* builder, and your YAML or JSON workspace files load through it out of the
box, just as they always have. **Everything on this page is optional; leave a setting
out to fall back to the default.**

:::{mermaid}
:caption: How a workspace file becomes a live tmux session.

flowchart TD
    load["tmuxp load &lt;workspace-file&gt;"] -->|reads workspace config| builder["Workspace Builder"]
    builder -->|"creates session, windows, panes"| attach["Attach tmux session"]
:::

Workspaces with special needs can reach for a builder's options to fine-tune how a
session loads. The classic builder, for instance, can wait for a pane's shell prompt
before sending its layout and commands — by default only when that shell is zsh (the
`pane_readiness` option). Waiting makes a session a little slower to load, but
guarantees the workspace is fully prepped before you attach.

You can also send a workspace through a different or custom builder instead of the
classic one, and tune its options the same way. For the braver cases, you can subclass
the classic builder or write your own in Python on top of
[libtmux](https://libtmux.git-pull.com/) — see
{ref}`custom-workspace-builders` for writing, packaging, testing, and the trust
boundary that comes with running builder code.

| Key | Type | Default | Purpose |
| --- | --- | --- | --- |
| `workspace_builder` | string | `classic` | Which builder turns the workspace into a session. |
| `workspace_builder_paths` | string or list of strings | _(none)_ | Trusted directories to import a builder from. |
| `workspace_builder_options` | mapping | _(all defaults)_ | Builder-behavior settings, such as `pane_readiness`. |

(workspace-builder-key)=

## `workspace_builder`

This is where you name the builder. Leave it out — or set `classic` — and you get
tmuxp's built-in builder, with nothing imported. When you name something else, tmuxp
works out what you mean from the shape of the value, in this order:

1. absent or empty → the built-in classic builder (nothing is imported);
2. contains `:` → a `module:attr` object reference;
3. no `.` and no `:` → a builder registered under the `tmuxp.workspace_builders`
   entry-point group, selected by name;
4. dotted with no `:` → an entry-point name if one is registered, otherwise a
   `module.attr` import path.

```yaml
session_name: my-session
workspace_builder: classic
windows:
  - panes:
      - vim
```

See {ref}`custom-workspace-builders` for selecting and packaging builders, and
{func}`~tmuxp.workspace.builder.registry.resolve_builder_class` for the resolver.

(workspace-builder-paths-key)=

## `workspace_builder_paths`

When your builder lives outside tmuxp's environment — say, a script sitting in your
config directory — this tells tmuxp where to find it. Give it a single directory or a
list of them. tmuxp expands `~` and environment variables, reads relative entries
against the workspace file's own directory, and expects each one to be a directory
that already exists. The paths join `sys.path` only for the import and build, not for
the rest of your session.

```yaml
workspace_builder: my_local_builder:CustomBuilder
workspace_builder_paths:
  - ~/.config/tmuxp/builders
```

```{warning}
A workspace file that names a builder runs that builder's Python code. Only load
workspace files you trust. See the security note in {ref}`custom-workspace-builders`.
```

(workspace-builder-options-key)=

## `workspace_builder_options`

This holds builder-behavior settings, whichever builder you use. For now there's just
one, `pane_readiness`, which decides whether tmuxp waits for a pane's shell prompt
before it sends that pane's layout and commands — a guard against a zsh prompt-redraw
artifact:

```yaml
workspace_builder_options:
  pane_readiness: auto
```

| Value | Behavior |
| --- | --- |
| `auto` _(default)_ | Wait only when the session's shell is zsh. |
| `always` | Always wait for default-shell panes. |
| `never` | Never wait; fastest, but accepts the prompt/layout race for shells that need it. |

`pane_readiness` also accepts truthy/falsy aliases — `true`/`on`/`yes`/`1` map to
`always`, and `false`/`off`/`no`/`0` map to `never` (full list in
{ref}`custom-workspace-builders`). An unrecognized value fails the load with:

```text
invalid pane_readiness value: 'sometimes'; expected one of: auto, always/true/on/yes/1, never/false/off/no/0
```

A pane that runs a custom `shell` or `window_shell` never waits, whatever you set here.
See {class}`~tmuxp.workspace.options.PaneReadiness` and
{class}`~tmuxp.workspace.options.WorkspaceBuilderOptions` for the parsing rules.

## Minimal complete example

````{tab} YAML
```yaml
session_name: my-session
workspace_builder: classic
workspace_builder_paths:
  - ~/.config/tmuxp/builders
workspace_builder_options:
  pane_readiness: auto
windows:
  - window_name: editor
    panes:
      - vim
```
````

````{tab} JSON
```json
{
  "session_name": "my-session",
  "workspace_builder": "classic",
  "workspace_builder_paths": ["~/.config/tmuxp/builders"],
  "workspace_builder_options": {
    "pane_readiness": "auto"
  },
  "windows": [
    {
      "window_name": "editor",
      "panes": ["vim"]
    }
  ]
}
```
````

```{seealso}
{ref}`custom-workspace-builders` — narrative guide to selecting, packaging,
writing, and testing builders ·
{class}`~tmuxp.workspace.builder.classic.ClassicWorkspaceBuilder` ·
{class}`~tmuxp.workspace.builder.protocol.WorkspaceBuilderProtocol`
```
