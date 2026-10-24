# AGENTS.md

tmuxp is a session manager for tmux: it saves and loads tmux sessions,
windows, and panes from declarative YAML or JSON workspace files, built on
[libtmux](https://github.com/tmux-python/libtmux).

Follow the conventions already in the tree, and keep a change scoped to what
was asked for.

## What is here

| Path                     | What it is                                       |
| ------------------------- | ------------------------------------------------- |
| `src/tmuxp/cli/`          | Subcommands: load, freeze, convert, import, edit, ls, search, shell, debug-info |
| `src/tmuxp/workspace/`    | `ConfigReader`, `WorkspaceBuilder`, workspace finders and freezer |
| `src/tmuxp/plugin.py`     | `TmuxpPlugin` base class and hook dispatch        |
| `src/tmuxp/exc.py`        | Exception hierarchy rooted at `TmuxpException`     |
| `src/tmuxp/_internal/`    | `ConfigReader` backend, `Colors`, non-public helpers |
| `tests/`                  | pytest suite; runs against a real tmux server      |
| `docs/`                   | Sphinx documentation source                        |
| `CHANGES`                 | Changelog, rendered as the docs changelog page      |
| `MIGRATION`               | Deprecation and migration notes                    |
| `.tmuxp.yaml`             | This project's own dev workspace file (`tmuxp load .`) |

## Which policy applies

- Documentation, user-facing text, `CHANGES`, release notes, commit messages,
  docstrings, and source comments:
  [.github/WRITING.md](.github/WRITING.md)
- Environment, the gates, tests, documentation builds, releases, and pull
  requests: [.github/CONTRIBUTING.md](.github/CONTRIBUTING.md)

Each of those is the single home for its subject. Where a rule seems to be
stated twice, the file listed above is the one that governs.

Logging conventions and CLI color semantics are scoped to `src/tmuxp/` and
live in [src/tmuxp/AGENTS.md](src/tmuxp/AGENTS.md).

## Change discipline

- Make the smallest coherent change that solves the verified problem; keep
  unrelated cleanup out of it.
- Reuse an existing file, helper, API, or test before adding a new one.
- Add a file only for a durable boundary — a distinct responsibility,
  independent reuse, or splitting an oversized module — not for a
  single-use helper or a one-line re-export.
- Add a test for every user-visible behaviour change, and a `CHANGES` entry
  for every change to the public API, CLI, configuration, or output.
- A passing gate is evidence only once it has been shown capable of failing.
  Pair a new test with a deliberate break that proves it bites.

## Domain facts

- tmux 3.3a+, Python 3.10+ (`requires-python` in `pyproject.toml`); mypy runs
  in strict mode.
- One console script (`tmuxp`) and one plugin entry-point group
  (`tmuxp.workspace_builders`).
- A workspace file is YAML or JSON; values trickle down session → window →
  pane, so a key set at the session level is a default a window or pane can
  override.

## References

- Changelog: `CHANGES` (rendered at <https://tmuxp.git-pull.com/history/>)
- Docs: <https://tmuxp.git-pull.com>
- Upstream: <https://github.com/tmux-python/libtmux>
