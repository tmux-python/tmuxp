(developing)=

# Developing and Testing

The tests live in `tests/`, written with [pytest]. They run against a real tmux
server on a separate socket (`$ tmux -L test_case`), so they never disturb your
own sessions.

[pytest]: http://pytest.org/

(install-dev-env)=

## Install the latest code from git

### Get the source

Check out the code from GitHub:

```console
$ git clone git@github.com:tmux-python/tmuxp.git
```

```console
$ cd tmuxp
```

### Bootstrap

The easiest way to set up a dev environment is with [uv], which manages the
virtualenv and Python dependencies for you. (See [uv's documentation] to install
uv itself.)

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

That's it — you're ready to code.

[uv]: https://github.com/astral-sh/uv
[uv's documentation]: https://docs.astral.sh/uv

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

## Test runner

[pytest] runs the tests. Inside the virtualenv, the `tmuxp` command and a
project-local `python` are already on your `PATH`.

### Rerun on file change

Watch files and re-run tests on every save, via [pytest-watcher]:

```console
$ just start
```

[pytest-watcher]: https://github.com/olzhasar/pytest-watcher

### Manual

```console
$ uv run py.test
```

Or:

```console
$ just test
```

### pytest options

Pass extra arguments through `PYTEST_ADDOPTS`. See the [pytest usage docs] for
everything it accepts.

[pytest usage docs]: https://docs.pytest.org/

Verbose:

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

With [ipython] installed:

```console
$ env PYTEST_ADDOPTS="--pdbcls=IPython.terminal.debugger:TerminalPdb" just start
```

[ipython]: https://ipython.org/

(test-specific-tests)=

### Manual invocation

Test a single file:

```console
$ py.test tests/test_config.py
```

A single test inside it:

```console
$ py.test tests/test_config.py::test_export_json
```

Several at once, space-separated:

```console
$ py.test tests/test_{window,pane}.py tests/test_config.py::test_export_json
```

(test-builder-visually)=

### Visual testing

You can watch the suite build sessions in real time by keeping a client open in
a second terminal.

Terminal 1 — start a server on the test socket:

```console
$ tmux -L test_case
```

Terminal 2 — from the tmuxp checkout (and your virtualenv, if you use one), run
the builder tests:

```console
$ py.test tests/workspace/test_builder.py
```

Terminal 1 flickers as sessions build before your eyes — the building tmuxp
normally hides from users.

### Testing options

Set `RETRY_TIMEOUT_SECONDS` if certain workspace-builder tests are stubborn on
your machine, e.g. `RETRY_TIMEOUT_SECONDS=10 py.test`. CI runs the same suite:

```{literalinclude} ../../.github/workflows/tests.yml
:language: yaml
```

## Documentation

Rebuild the docs whenever a source file changes:

```console
$ just watch-docs
```

(tmuxp-developer-config)=

## tmuxp developer config

```{image} /_static/tmuxp-dev-screenshot.png
:width: 1030
:height: 605
:align: center
:loading: lazy
```

After you {ref}`install-dev-env`, load the project's own workspace from the
checkout root:

```console
$ tmuxp load .
```

This loads the `.tmuxp.yaml` at the project root:

```{literalinclude} ../../.tmuxp.yaml
:language: yaml
```

## Formatting

### Linting

The project uses [ruff] for linting, import sorting, and formatting.

Lint:

```console
$ just ruff
```

Autofix what ruff can:

```console
$ uv run ruff check . --fix --show-fixes
```

#### Formatting

[ruff format] handles formatting:

```console
$ just ruff-format
```

### Type checking

[mypy] does static type checking:

```console
$ just mypy
```

Re-check on change:

```console
$ just watch-mypy
```

(gh-actions)=

## Continuous integration

tmuxp uses [GitHub Actions] for continuous integration. To see the tmux and
Python versions under test, read [.github/workflows/tests.yml]. Builds run on
`master` and on pull requests, and are visible on the [build site].

[ruff]: https://ruff.rs
[ruff format]: https://docs.astral.sh/ruff/formatter/
[mypy]: http://mypy-lang.org/
[GitHub Actions]: https://github.com/features/actions
[build site]: https://github.com/tmux-python/tmuxp/actions?query=workflow%3Atests
[.github/workflows/tests.yml]: https://github.com/tmux-python/tmuxp/blob/master/.github/workflows/tests.yml
