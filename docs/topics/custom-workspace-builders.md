(custom-workspace-builders)=

# Custom workspace builders

A *workspace builder* turns an expanded workspace ``dict`` into a live tmux
session. tmuxp ships one builder,
{class}`~tmuxp.workspace.builder.classic.ClassicWorkspaceBuilder`, and uses it
by default. Advanced users can point tmuxp at a different builder, and packagers
can distribute builders that users select by name.

This is an advanced, opt-in feature. Existing workspace files keep using the
classic builder with no changes.

## How a workspace is built

1. `tmuxp load` reads the YAML/JSON file and expands it (shorthand, environment
   variables, trickle-down defaults).
2. tmuxp resolves which builder to use from the `workspace_builder` config key
   (default: the classic builder).
3. tmuxp constructs the builder with the expanded workspace and a
   {class}`libtmux.Server`, then calls `.build()`.
4. The builder creates the session, windows, and panes, honoring plugin hooks
   and progress callbacks.

## Selecting a builder

### By dotted path

Point `workspace_builder` at an importable class. Both a
`module:attr` object reference and a dotted `module.attr` path are accepted:

```yaml
session_name: my-session
workspace_builder: my_tmuxp_builders.builders:CustomBuilder
windows:
  - window_name: editor
    panes:
      - vim
```

### By entry-point name

Packaged builders register under the `tmuxp.workspace_builders` entry-point
group, letting users select them by a short name instead of an internal module
path:

```yaml
workspace_builder: classic
```

The built-in classic builder is registered this way. A distribution registers
its own builder in `pyproject.toml`:

```toml
[project.entry-points."tmuxp.workspace_builders"]
mybuilder = "my_tmuxp_builders.builders:CustomBuilder"
```

### Trusted import paths

When a builder lives outside tmuxp's runtime environment (for example, a script
in your config directory), list trusted directories in
`workspace_builder_paths`. tmuxp expands `~` and environment variables,
resolves relative entries against the workspace file's directory, requires each
entry to be an existing directory, and temporarily prepends them to `sys.path`
for the import and build:

```yaml
workspace_builder: my_local_builder:CustomBuilder
workspace_builder_paths:
  - ~/.config/tmuxp/builders
```

:::{warning}
A workspace file that names a builder runs that builder's Python code. Only load
workspace files you trust. tmuxp deliberately does **not** use
`site.addsitedir()` for these paths — that would execute `.pth` startup files
and is broader than making a module importable.
:::

## Writing a builder

The simplest custom builder subclasses the classic builder and overrides what it
needs:

```python
from tmuxp.workspace.builder.classic import ClassicWorkspaceBuilder


class CustomBuilder(ClassicWorkspaceBuilder):
    """A builder that renames the session after building."""

    def build(self, session=None, append=False):
        super().build(session=session, append=append)
        self.session.rename_session(f"{self.session.name}-custom")
```

A builder written from scratch must satisfy
{class}`~tmuxp.workspace.builder.protocol.WorkspaceBuilderProtocol`. The contract
covers what `tmuxp load` drives:

- **Constructor** accepting `session_config`, `server`, and the optional
  `plugins` list and `on_progress` / `on_before_script` / `on_script_output` /
  `on_build_event` callbacks.
- **`build(session=None, append=False)`** — create or populate the session; the
  `append` path adds windows to an existing session.
- **`session`** — the populated {class}`libtmux.Session`.
- **`session_exists()`** and **`find_current_attached_session()`** — used by the
  CLI for attach/append decisions.
- **`plugins`** — the list of plugin instances; honor the plugin lifecycle hooks
  (`before_workspace_builder`, `on_window_create`, `after_window_finished`).
- The **`on_*` callbacks** — call them at the documented milestones so the CLI's
  progress display and `before_script` output stay accurate.

The contract is synchronous today. It is shaped so an async builder can be added
later as an additive extension without changing this surface.

## Pane readiness

tmuxp waits for a pane's shell prompt before dispatching layout and commands,
which avoids a zsh prompt-redraw artifact. That wait is only needed for zsh, so
it is configurable independently of which builder you use, through the
`workspace_builder_options` catalog:

```yaml
workspace_builder_options:
  pane_readiness: auto   # auto | always | never (+ truthy/falsy aliases)
```

- **`auto`** (default) — wait only when the session's interactive shell is zsh.
- **`always`** (or `true`/`on`/`yes`/`1`) — always wait for default-shell panes.
- **`never`** (or `false`/`off`/`no`/`0`) — never wait; fastest, but accepts the
  prompt/layout race for shells that need it.

Panes with a custom `shell` or `window_shell` never wait, regardless of policy —
those run a command in place of an interactive shell, so there is no prompt to
wait for.

See {class}`~tmuxp.workspace.options.PaneReadiness` and
{class}`~tmuxp.workspace.options.WorkspaceBuilderOptions` for the parsing rules.

## Testing a builder

Resolve, construct, and build against a real tmux server fixture:

```python
from tmuxp.workspace import loader
from tmuxp.workspace.builder import registry


def test_custom_builder(server):
    config = loader.expand(
        {
            "session_name": "demo",
            "workspace_builder": "my_tmuxp_builders.builders:CustomBuilder",
            "windows": [{"window_name": "main", "panes": [{"shell_command": []}]}],
        },
    )
    builder_cls = registry.resolve_builder_class(config)
    builder = builder_cls(session_config=config, server=server)
    builder.build()
    assert builder.session.name == "demo"
    builder.session.kill()
```

For builders that live in a trusted directory, build the `sys.path` sandbox with
{func}`~tmuxp.workspace.builder.registry.resolve_builder_paths` and
{func}`~tmuxp.workspace.builder.registry.prepended_sys_path`.

## Choosing an approach

- **Classic builder** — the default. Use it for any workspace that depends on
  strict, pane-by-pane side effects (`start_directory`, `shell`, `window_shell`,
  pane environment).
- **Readiness tuning** — set `pane_readiness` to trade prompt-safety for speed
  without swapping builders.
- **A custom builder** — when you need behavior the classic builder doesn't
  provide. Keep dependency-sensitive setup in `before_script` or
  `shell_command_before` if your builder relaxes ordering guarantees.

## Reference

- {class}`~tmuxp.workspace.builder.classic.ClassicWorkspaceBuilder`
- {class}`~tmuxp.workspace.builder.protocol.WorkspaceBuilderProtocol`
- {func}`~tmuxp.workspace.builder.registry.resolve_builder_class`
- {class}`~tmuxp.workspace.options.PaneReadiness`
