# AGENTS.md

This file provides guidance to AI agents (e.g., Claude Code, Cursor, and other LLM-powered tools) when working with code in this repository.

## Project Overview

tmuxp is a session manager for tmux that allows users to save and load tmux sessions through YAML/JSON configuration files. It's powered by libtmux and provides a declarative way to manage tmux sessions.

## Development Commands

### Testing
- `just test` or `uv run py.test` - Run all tests
- `uv run py.test tests/path/to/test.py::TestClass::test_method` - Run a single test
- `uv run ptw .` - Continuous test runner with pytest-watcher
- `uv run ptw . --now --doctest-modules` - Watch tests including doctests
- `just start` or `just watch-test` - Watch and run tests on file changes

### Code Quality
- `just ruff` or `uv run ruff check .` - Run linter
- `uv run ruff check . --fix --show-fixes` - Fix linting issues automatically
- `just ruff-format` or `uv run ruff format .` - Format code
- `just mypy` or `uv run mypy` - Run type checking (strict mode enabled)
- `just watch-ruff` - Watch and lint on changes
- `just watch-mypy` - Watch and type check on changes

### Documentation
- `just build-docs` - Build documentation
- `just serve-docs` - Serve docs locally at http://localhost:8013
- `just dev-docs` - Watch and serve docs with auto-reload
- `just start-docs` - Alternative to dev_docs

### CLI Commands
- `tmuxp load <config>` - Load a tmux session from config
- `tmuxp load -d <config>` - Load session in detached state
- `tmuxp freeze <session-name>` - Export running session to config
- `tmuxp convert <file>` - Convert between YAML and JSON
- `tmuxp shell` - Interactive Python shell with tmux context
- `tmuxp debug-info` - Collect system info for debugging

## Architecture

### Core Components

1. **CLI Module** (`src/tmuxp/cli/`): Entry points for all tmuxp commands
   - `load.py`: Load tmux sessions from config files
   - `freeze.py`: Export live sessions to config files
   - `convert.py`: Convert between YAML/JSON formats
   - `shell.py`: Interactive Python shell with tmux context

2. **Workspace Module** (`src/tmuxp/workspace/`): Core session management
   - `builder.py`: Builds tmux sessions from configuration
   - `loader.py`: Loads and validates config files
   - `finders.py`: Locates workspace config files
   - `freezer.py`: Exports running sessions to config

3. **Plugin System** (`src/tmuxp/plugin.py`): Extensibility framework
   - Plugins extend `TmuxpPlugin` base class
   - Hooks: `before_workspace_builder`, `on_window_create`, `after_window_finished`, `before_script`, `reattach`
   - Version constraint checking for compatibility

### Configuration Flow

1. Load YAML/JSON config via `ConfigReader` (handles includes, environment variables)
2. Expand inline shorthand syntax
3. Trickle down default values (session → window → pane)
4. Validate configuration structure
5. Build tmux session via `WorkspaceBuilder`

### Key Patterns

- **Type Safety**: All code uses type hints with mypy strict mode
- **Error Handling**: Custom exception hierarchy based on `TmuxpException`
- **Testing**: Pytest with fixtures for tmux server/session/window/pane isolation
- **Future Imports**: All files use `from __future__ import annotations`

## Configuration Format

```yaml
session_name: my-session
start_directory: ~/project
windows:
  - window_name: editor
    layout: main-vertical
    panes:
      - shell_command:
          - vim
      - shell_command:
          - git status
```

## Environment Variables

- `TMUXP_CONFIGDIR`: Custom directory for workspace configs
- `TMUX_CONF`: Path to tmux configuration file
- `TMUXP_DEFAULT_COLUMNS/ROWS`: Default session dimensions

## Testing Guidelines

- **Use functional tests only**: Write tests as standalone functions, not classes. Avoid `class TestFoo:` groupings - use descriptive function names and file organization instead.
- Use pytest fixtures from `tests/fixtures/` for tmux objects
- Test plugins using mock packages in `tests/fixtures/pluginsystem/`
- Use `retry_until` utilities for async tmux operations
- Run single tests with: `uv run py.test tests/file.py::test_function_name`
- **Use libtmux fixtures**: Prefer `server`, `session`, `window`, `pane` fixtures over manual setup
- **Avoid mocks when fixtures exist**: Use real tmux fixtures instead of `MagicMock`
- **Use `tmp_path`** fixture instead of Python's `tempfile`
- **Use `monkeypatch`** fixture instead of `unittest.mock`

## Code Style

- Follow NumPy-style docstrings (pydocstyle convention)
- Use ruff for formatting and linting
- Maintain strict mypy type checking
- Keep imports organized with future annotations at top
- **Prefer namespace imports for stdlib**: Use `import enum` and `enum.Enum` instead of `from enum import Enum`; third-party packages may use `from X import Y`
- **Type imports**: Use `import typing as t` and access via namespace (e.g., `t.Optional`)
- **Development workflow**: Format → Test → Commit → Lint/Type Check → Test → Final Commit

## Doctests

**All functions and methods MUST have working doctests.** Doctests serve as both documentation and tests.

**CRITICAL RULES:**
- Doctests MUST actually execute - never comment out function calls or similar
- Doctests MUST NOT be converted to `.. code-block::` as a workaround (code-blocks don't run)
- If you cannot create a working doctest, **STOP and ask for help**

**Available tools for doctests:**
- `doctest_namespace` fixtures: `server`, `session`, `window`, `pane`, `tmp_path`, `test_utils`
- Ellipsis for variable output: `# doctest: +ELLIPSIS`
- Update `conftest.py` to add new fixtures to `doctest_namespace`

**`# doctest: +SKIP` is NOT permitted** - it's just another workaround that doesn't test anything. Use the fixtures properly - tmux is required to run tests anyway.

**Using fixtures in doctests:**
```python
>>> from tmuxp.workspace.builder import WorkspaceBuilder
>>> config = {'session_name': 'test', 'windows': [{'window_name': 'main'}]}
>>> builder = WorkspaceBuilder(session_config=config, server=server)  # doctest: +ELLIPSIS
>>> builder.build()
>>> builder.session.name
'test'
```

**When output varies, use ellipsis:**
```python
>>> session.session_id  # doctest: +ELLIPSIS
'$...'
>>> window.window_id  # doctest: +ELLIPSIS
'@...'
```

**Additional guidelines:**
1. **Use narrative descriptions** for test sections rather than inline comments
2. **Move complex examples** to dedicated test files at `tests/examples/<path>/test_<example>.py`
3. **Keep doctests simple and focused** on demonstrating usage
4. **Add blank lines between test sections** for improved readability

## Documentation Standards

### Code Blocks in Documentation

When writing documentation (README, CHANGES, docs/), follow these rules for code blocks:

**One command per code block.** This makes commands individually copyable.

**Put explanations outside the code block**, not as comments inside.

Good:

Run the tests:

```console
$ uv run pytest
```

Run with coverage:

```console
$ uv run pytest --cov
```

Bad:

```console
# Run the tests
$ uv run pytest

# Run with coverage
$ uv run pytest --cov
```

## Important Notes

- **QA every edit**: Run formatting and tests before committing
- **Minimum Python**: 3.10+ (per pyproject.toml)
- **Minimum tmux**: 3.2+ (as per README)

## CLI Color Semantics (Revision 1, 2026-01-04)

The CLI uses semantic colors via the `Colors` class in `src/tmuxp/_internal/colors.py`. Colors are chosen based on **hierarchy level** and **semantic meaning**, not just data type.

### Design Principles

1. **Structural hierarchy**: Headers > Items > Details
2. **Semantic meaning**: What IS this element?
3. **Visual weight**: What should draw the eye first?
4. **Depth separation**: Parent elements should visually contain children

Inspired by patterns from **jq** (object keys vs values), **ripgrep** (path/line/match distinction), and **mise/just** (semantic method names).

### Hierarchy-Based Colors

| Level | Element Type | Method | Color | Examples |
|-------|--------------|--------|-------|----------|
| **L0** | Section headers | `heading()` | Bright cyan + bold | "Local workspaces:", "Global workspaces:" |
| **L1** | Primary content | `highlight()` | Magenta + bold | Workspace names (braintree, .tmuxp) |
| **L2** | Supplementary info | `info()` | Cyan | Paths (~/.tmuxp, ~/project/.tmuxp.yaml) |
| **L3** | Metadata/labels | `muted()` | Blue | Source labels (Legacy:, XDG default:) |

### Status-Based Colors (Override hierarchy when applicable)

| Status | Method | Color | Examples |
|--------|--------|-------|----------|
| Success/Active | `success()` | Green | "active", "18 workspaces" |
| Warning | `warning()` | Yellow | Deprecation notices |
| Error | `error()` | Red | Error messages |

### Example Output

```
Local workspaces:                              ← heading() bright_cyan+bold
  .tmuxp  ~/work/python/tmuxp/.tmuxp.yaml      ← highlight() + info()

Global workspaces (~/.tmuxp):                  ← heading() + info()
  braintree                                    ← highlight()
  cihai                                        ← highlight()

Global workspace directories:                  ← heading()
  Legacy: ~/.tmuxp (18 workspaces, active)     ← muted() + info() + success()
  XDG default: ~/.config/tmuxp (not found)     ← muted() + info() + muted()
```

### Available Methods

```python
colors = Colors()
colors.heading("Section:")      # Cyan + bold (section headers)
colors.highlight("item")        # Magenta + bold (primary content)
colors.info("/path/to/file")    # Cyan (paths, supplementary info)
colors.muted("label:")          # Blue (metadata, labels)
colors.success("ok")            # Green (success states)
colors.warning("caution")       # Yellow (warnings)
colors.error("failed")          # Red (errors)
```

### Key Rules

**Never use the same color for adjacent hierarchy levels.** If headers and items are both blue, they blend together. Each level must be visually distinct.

**Avoid dim/faint styling.** The ANSI dim attribute (`\x1b[2m`) is too dark to read on black terminal backgrounds. This includes both standard and bright color variants with dim.

**Bold may not render distinctly.** Some terminal/font combinations don't differentiate bold from normal weight. Don't rely on bold alone for visual distinction - pair it with color differences.
