# Contributing

Thanks for looking. Bug reports with a reproduction, and notes on where the
documentation misled you, are the most useful thing you can bring right now.

How this project writes prose — README, `CHANGES`, commit messages,
docstrings, and source comments — is set out separately in
[WRITING.md](WRITING.md). Read that before changing any of it. The constraints
every change is held to, and the map of what is where, are in
[AGENTS.md](../AGENTS.md).

## Getting set up

Check out the code from GitHub:

```console
$ git clone git@github.com:tmux-python/tmuxp.git
```

```console
$ cd tmuxp
```

The easiest way to set up a dev environment is with [uv], which manages the
virtualenv and Python dependencies for you.

Create the virtualenv and install everything locked in `uv.lock`:

```console
$ uv sync --all-extras --dev
```

To refresh those packages later:

```console
$ uv sync --all-extras --dev --upgrade
```

Then prefix any Python command with `uv run`:

```console
$ uv run [command]
```

[uv]: https://docs.astral.sh/uv

### Advanced: manual virtualenv

Prefer to manage the virtualenv yourself? Create one:

```console
$ virtualenv .venv
```

Activate it in your current shell:

```console
$ source .venv/bin/activate
```

Install tmuxp in editable mode, so your edits take effect immediately:

```console
$ pip install -e .
```

With a uv-managed project, add the checkout as an editable dev dependency
instead:

```console
$ uv add --dev --editable .
```

Prefer a one-off, pipx-style run while you hack? Call tmuxp through [uvx]:

```console
$ uvx tmuxp
```

[uvx]: https://docs.astral.sh/uv/guides/tools/

## The gates

CI is the order of record; every gate it runs has to pass before a change is
done.

Format:

```console
$ uv run ruff format .
```

CI checks formatting without writing:

```console
$ uv run ruff format --check .
```

Lint:

```console
$ uv run ruff check .
```

Autofix what ruff can:

```console
$ uv run ruff check . --fix --show-fixes
```

Type-check:

```console
$ uv run mypy
```

Test:

```console
$ uv run py.test
```

Documentation is a gate, not a courtesy. `[tool.pytest.ini_options]` in
`pyproject.toml` sets `testpaths = ["src/tmuxp", "tests", "docs"]` and
`addopts` includes `--doctest-modules`, so every `>>> ` example under
`src/tmuxp/**` and every doctest in a `.py` file under `docs/` runs as part of
`uv run py.test` — there is no separate doctest step, and a green test run is
the proof. `README.md` is not in `testpaths` and is never executed; hold its
examples correct by review. Which blocks qualify, and the one mistake that
silently removes a test, are in
[WRITING.md](WRITING.md#documented-examples-that-run).

Before claiming a test or a gate works, show it failing. A gate that has
never been red is an assumption.

### Imports and typing

- **Namespace imports for the standard library**: `import pathlib`, then
  `pathlib.Path`, not `from pathlib import Path`. Exception:
  `from dataclasses import dataclass, field`, since both are used as
  decorators/defaults, not namespaced. Third-party packages may use
  `from X import Y`.
- **Typing**: `import typing as t`, access via the namespace —
  `t.Optional`, `t.NamedTuple`.
- **Every file** starts with `from __future__ import annotations`; ruff's
  `isort` config (`required-imports` in `pyproject.toml`) enforces it.

Ruff's `select` is deliberately unset in `pyproject.toml` — 0.16's curated
default rule set stays enabled, and `extend-select` layers this project's
additional linters (pydocstyle, flake8-bugbear, and the rest) on top rather
than replacing the defaults.

## Tests

The suite lives in `tests/`, written with [pytest]. It runs against a real
tmux server on a separate socket (`tmux -L test_case`), so it never disturbs
your own sessions.

[pytest]: https://pytest.org/

Write new tests as standalone functions, not `class TestFoo:` groupings —
descriptive function names and file organization carry the structure instead.
A couple of older suites still use classes; match the file you are in, prefer
functions in a new one.

- Prefer the `server`, `session`, `window`, `pane` fixtures from
  `tests/fixtures/` over manual setup, and real tmux fixtures over
  `MagicMock`.
- Use `retry_until` (from `libtmux.test.retry`) for anything that waits on an
  async tmux operation instead of a bare sleep.
- Use the `tmp_path` fixture instead of Python's `tempfile`, and
  `monkeypatch` instead of `unittest.mock`.
- Plugin tests import mock packages from
  `tests/fixtures/pluginsystem/plugins/` — six fixture plugins
  (`tmuxp_test_plugin_bwb`, `_bs`, `_r`, `_owc`, `_awf`, `_fail`) exercising
  each plugin hook and a deliberate failure path.
- Assert on `caplog.records` attributes, not string matching on
  `caplog.text`: scope capture with
  `caplog.at_level(logging.DEBUG, logger="libtmux.common")`, filter records
  rather than index by position, and assert on schema
  (`record.tmux_exit_code == 0`, not `"exit code 0" in caplog.text`).
  `caplog.record_tuples` cannot access `extra` fields.

### Rerun on file change

```console
$ just start
```

Runs the suite once, then watches for changes via [pytest-watcher].

[pytest-watcher]: https://github.com/olzhasar/pytest-watcher

### pytest options

Pass extra arguments through `PYTEST_ADDOPTS`:

```console
$ env PYTEST_ADDOPTS="--verbose" just start
```

Pick a file:

```console
$ env PYTEST_ADDOPTS="tests/workspace/test_builder.py" just start
```

Drop into a single test and stop on the first error:

```console
$ env PYTEST_ADDOPTS="-s -x -vv tests/workspace/test_builder.py::test_automatic_rename_option" \
    just start
```

Drop into `pdb` on the first error:

```console
$ env PYTEST_ADDOPTS="-x -s --pdb" just start
```

Set `RETRY_TIMEOUT_SECONDS` if a workspace-builder test is stubborn on your
machine:

```console
$ env RETRY_TIMEOUT_SECONDS=10 uv run py.test
```

### Manual invocation

A single file:

```console
$ uv run py.test tests/workspace/test_builder.py
```

A single test inside it:

```console
$ uv run py.test tests/test_config.py::test_export_json
```

### Visual testing

Watch the suite build sessions in real time by keeping a client open in a
second terminal.

Terminal 1 — start a server on the test socket:

```console
$ tmux -L test_case
```

Terminal 2 — from the checkout, run the builder tests:

```console
$ uv run py.test tests/workspace/test_builder.py
```

Terminal 1 flickers as sessions build before your eyes — the building tmuxp
normally hides from users.

### Native tmux in CI

The test workflow builds the versions in its existing matrix. Stable
versions use the official release archives and SHA256 pins in
`.github/tmux-releases.toml`, including tmux 3.8; `master` resolves once
to a commit and fetches that exact commit. The build follows tmux's
[release and source-checkout instructions](https://github.com/tmux/tmux/blob/3.8/README#L23-L37).
Only the installed prefix is cached. Each build uses a fresh source tree
and up to four available processors.

Cache keys include the actual runner image and image version, architecture,
compiler and dependency versions, source identity, and build script.
Dependencies are installed before validation on hits and misses. Every
restored executable must match its recorded hash and version, start a
private daemon, and report the same connected version. A failed check
discards that job's prefix and rebuilds it.

The workflow saves a validated installation before library tests run.
GitHub caches are immutable: repairing an invalid exact hit fixes the
current job, but cannot overwrite that entry. A build-script change
invalidates its key for later jobs. Never add a broad restore-key fallback
for native binaries.

The CI scripts use the standard-library TOML reader, which Python 3.11
added. Run the cache regressions against an installed tmux:

```console
$ uv run pytest .github/scripts/test_tmux_build.py --reruns=0
```

## Documentation

Rebuild the docs whenever a source file changes:

```console
$ just watch-docs
```

Or build once:

```console
$ just build-docs
```

Serve the built docs locally:

```console
$ just serve-docs
```

`just dev-docs` runs the watcher and the server together; `just design-docs`
adds a static-file watch for theme work. `docs/_build/` is generated —
never hand-edit it.

After you set up your environment, load the project's own workspace from the
checkout root to see a real multi-pane dev layout:

```console
$ tmuxp load .
```

That loads `.tmuxp.yaml` at the project root.

## Releasing

Never create tags. Never push tags. The owner handles tagging and tag pushes,
because a tag triggers the publish workflow. See
[Release commits](WRITING.md#release-commits).

The full release process — updating `CHANGES`, bumping the version, tagging,
and the CI publish to PyPI — is in
[Releasing](../docs/project/releasing.md).

## Pull requests

One subject per pull request. Unrelated cleanup found along the way belongs
in its own commit, and usually in its own pull request.

Discuss a substantial change via an issue before making it.

Run the gates above before opening a pull request; update documentation if
your change affects the public interface. A pull request merges once it has
the sign-off of one other developer — if you cannot merge it yourself,
request a reviewer to do so.

Commit format is in [WRITING.md](WRITING.md#commits).

## Decorum

- Participants will be tolerant of opposing views.
- Participants must ensure that their language and actions are free of
  personal attacks and disparaging personal remarks.
- When interpreting the words and actions of others, participants should
  always assume good intentions.
- Behaviour which can be reasonably considered harassment will not be
  tolerated.

Based on [Ruby's Community Conduct Guideline](https://www.ruby-lang.org/en/conduct/).

## Security

Please do not open a public issue for a vulnerability. Use GitHub's private
vulnerability reporting (the repository's Security tab → "Report a
vulnerability"), or contact the maintainer listed in `pyproject.toml`.
