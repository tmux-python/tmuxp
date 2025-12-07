# AGENTS.md

This file provides guidance to AI agents (e.g., Claude Code, Cursor, and other LLM-powered tools) when working with code in this repository.

## Project Overview

tmuxp is a session manager for tmux that allows users to save and load tmux sessions through YAML/JSON configuration files. It's powered by libtmux and provides a declarative way to manage tmux sessions.

## Development Commands

### Testing
- `make test` or `uv run py.test` - Run all tests
- `uv run py.test tests/path/to/test.py::TestClass::test_method` - Run a single test
- `uv run ptw .` - Continuous test runner with pytest-watcher
- `uv run ptw . --now --doctest-modules` - Watch tests including doctests
- `make start` or `make watch_test` - Watch and run tests on file changes

### Code Quality
- `make ruff` or `uv run ruff check .` - Run linter
- `uv run ruff check . --fix --show-fixes` - Fix linting issues automatically
- `make ruff_format` or `uv run ruff format .` - Format code
- `make mypy` or `uv run mypy` - Run type checking (strict mode enabled)
- `make watch_ruff` - Watch and lint on changes
- `make watch_mypy` - Watch and type check on changes

### Documentation
- `make build_docs` - Build documentation
- `make serve_docs` - Serve docs locally at http://localhost:8013
- `make dev_docs` - Watch and serve docs with auto-reload
- `make start_docs` - Alternative to dev_docs

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

- Use pytest fixtures from `tests/fixtures/` for tmux objects
- Test plugins using mock packages in `tests/fixtures/pluginsystem/`
- Use `retry_until` utilities for async tmux operations
- Run single tests with: `uv run py.test tests/file.py::TestClass::test_method`
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

## Important Notes from Cursor Rules

- **QA every edit**: Run formatting and tests before committing
- **Doctest format**: Use narrative descriptions with blank lines between sections
- **Complex examples**: Move to `tests/examples/<path>/test_<example>.py`
- **Minimum Python**: 3.9+ (as per README)
- **Minimum tmux**: 3.2+ (as per README)
