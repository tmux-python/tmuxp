(workspace-builders)=

# Workspace builders

```{versionadded} 1.72.0
```

Most workspaces never need these keys. By default tmuxp builds your session with
its built-in *classic* builder and waits for a pane's shell prompt only when that
shell is zsh — existing workspace files keep working unchanged. Set the keys below
to swap in a different builder or to tune the prompt wait. **Omit a key (or remove
it) to restore the default.**

| Key | Type | Default | Purpose |
| --- | --- | --- | --- |
| `workspace_builder` | string | `classic` | Which builder turns the workspace into a session. |
| `workspace_builder_paths` | string or list of strings | _(none)_ | Trusted directories to import a builder from. |
| `workspace_builder_options` | mapping | _(all defaults)_ | Builder-behavior knobs, such as `pane_readiness`. |

For the narrative — writing a builder, packaging one, the trust boundary, and
testing — see {ref}`custom-workspace-builders`.

(workspace-builder-key)=

## `workspace_builder`

Selects the builder. The default, `classic`, is tmuxp's built-in builder. A value
is resolved in this order:

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

Directories to import a builder from when it lives outside tmuxp's environment —
for example, a script in your config directory. Accepts a single string or a list
of strings. tmuxp expands `~` and environment variables, resolves relative entries
against the workspace file's directory, and requires each entry to be an existing
directory; the paths are added to `sys.path` only for the import and build.

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

A catalog of builder-behavior settings, independent of which builder you use.
Today it holds a single key, `pane_readiness`, which controls whether tmuxp waits
for a pane's shell prompt before sending its layout and commands — a guard against
a zsh prompt-redraw artifact:

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

Panes that run a custom `shell` or `window_shell` never wait, regardless of policy.
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
