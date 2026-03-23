# Code Style

## Formatting

tmuxp uses [ruff](https://github.com/astral-sh/ruff) for both linting and formatting.

```console
$ uv run ruff format .
```

```console
$ uv run ruff check . --fix --show-fixes
```

## Type Checking

Strict [mypy](https://mypy-lang.org/) is enforced.

```console
$ uv run mypy
```

## Docstrings

All public functions and methods use NumPy-style docstrings.

## Imports

- Standard library: namespace imports (`import pathlib`, not `from pathlib import Path`)
  - Exception: `from dataclasses import dataclass, field`
- Typing: `import typing as t`, access via `t.Optional`, `t.NamedTuple`, etc.
- All files: `from __future__ import annotations`
