(developing)=

# Developing and Testing

```{eval-rst}
.. todo::
    link to sliderepl or ipython notebook slides
```

Our tests are inside `tests/`. Tests are implemented using
[pytest].

`make test` will create a tmux server on a separate `socket_name`
using `$ tmux -L test_case`.

[pytest]: http://pytest.org/

(install-dev-env)=

## Install the latest code from git

### Get the source

To begin developing, check out the code from github:

```console
$ git clone git@github.com:tmux-python/tmuxp.git
```

```console
$ cd tmuxp
```

### Bootstrap

The easiest way to configure a dev environment is through [poetry]. This
automatically will manage virtualenv and python dependencies for tmuxp.
For information on installing poetry visit the [poetry's documentation].

To begin developing, check out the code from github:

```console
$ git clone git@github.com:tmux-python/tmuxp.git
```

```console
$ cd tmuxp
```

You can create a virtualenv, and install all of the locked
packages as listed in poetry.lock:

```console
$ poetry install
```

If you ever need to update packages during your development session, the
following command can be used to update all packages as per poetry settings or
individual package (second command):

```console
$ poetry update
```

```console
$ poetry update requests
```

Then activate it to your current tty / terminal session with:

```console
$ poetry shell
```

That is it! You are now ready to code!

[poetry]: https://python-poetry.org/
[poetry's documentation]: https://python-poetry.org/docs/

### Advanced: Manual virtualenv

Now create a virtualenv, if you don't know how to, you can create a
virtualenv with:

```console
$ virtualenv .venv
```

Then activate it to your current tty / terminal session with:

```console
$ source .venv/bin/activate
```

Good! Now let's run this:

```console
$ pip install -e .
```

This has `pip`, a python package manager install the python package
in the current directory. `-e` means `--editable`, which means you can
adjust the code and the installed software will reflect the changes.

```console
$ tmuxp
```

## Test Runner

[pytest] is used for tests.

As you seen above, the `tmuxp` command will now be available to you,
since you are in the virtual environment, your {}`PATH` environment was
updated to include a special version of `python` inside your `.venv`
folder with its own packages.

### Rerun on file change

via [pytest-watcher] (works out of the box):

```console
$ make start
```

via [`entr(1)`] (requires installation):

```console
$ make watch_test
```

[pytest-watcher]: https://github.com/olzhasar/pytest-watcher

### Manual (just the command, please)

```console
$ poetry run py.test
```

or:

```console
$ make test
```

### pytest options

`PYTEST_ADDOPTS` can be set in the commands below. For more
information read [docs.pytest.com] for the latest documentation.

[docs.pytest.com]: https://docs.pytest.org/

Verbose:

```console
$ env PYTEST_ADDOPTS="-verbose" make start
```

Pick a file:

```console
$ env PYTEST_ADDOPTS="tests/test_workspacebuilder.py" poetry run make start
```

Drop into `test_automatic_rename_option()` in `tests/test_workspacebuilder.py`:

```console
$ env PYTEST_ADDOPTS="-s -x -vv tests/test_workspacebuilder.py" poetry run make start
```

Drop into `test_automatic_rename_option()` in `tests/test_workspacebuilder.py` and stop on first error:

```console
$ env PYTEST_ADDOPTS="-s -x -vv tests/test_workspacebuilder.py::test_automatic_rename_option" poetry run make start
```

Drop into `pdb` on first error:

```console
$ env PYTEST_ADDOPTS="-x -s --pdb" make start
```

If you have [ipython] installed:

```console
$ env PYTEST_ADDOPTS="--pdbcls=IPython.terminal.debugger:TerminalPdb" make start
```

[ipython]: https://ipython.org/

```console
$ make test
```

You probably didn't see anything but tests scroll by.

If you found a problem or are trying to write a test, you can file an
[issue on github].

(test-specific-tests)=

### Manual invocation

Test only a file:

```console
$ py.test tests/test_config.py
```

will test the `tests/test_config.py` tests.

```console
$ py.test tests/test_config.py::test_export_json
```

tests `test_export_json` inside of `tests/test_config.py`.

Multiple can be separated by spaces:

```console
$ py.test tests/test_{window,pane}.py tests/test_config.py::test_export_json
```

(test-builder-visually)=

### Visual testing

You can watch tmux testsuite build sessions visually by keeping a client
open in a separate terminal.

Create two terminals:

- Terminal 1: `$ tmux -L test_case`

- Terminal 2: `$ cd` into the tmuxp project and into the
  `virtualenv` if you are using one, see details on installing the dev
  version of tmuxp above. Then:

  ```console
  $ py.test tests/test_workspacebuilder.py
  ```

Terminal 1 should have flickered and built the session before your eyes.
tmuxp hides this building from normal users.

### Run tests on save (old method)

You can re-run tests automatically on file edit.

:::{note}

This requires [`entr(1)`].

:::

Install [entr]. Packages are available available on most Linux and BSD
variants, including Debian, Ubuntu, FreeBSD, OS X.

To run all tests upon editing any `.py` file:

```console
$ make watch_test
```

You can also re-run a specific test file or any other [py.test usage
argument]:

```console
$ make watch_test test=tests/test_config.py
```

```console
$ make watch_test test='-x tests/test_config.py tests/test_util.py'
```

### Testing options

`RETRY_TIMEOUT_SECONDS` can be toggled if certain workspace builder
tests are being stubborn.

e.g. `RETRY_TIMEOUT_SECONDS=10 py.test`

```{literalinclude} ../.github/workflows/tests.yml
:language: yaml

```

## Documentation

### Rebuild on save

Rebuild the documentation when an `.md` file is edited:

```console
$ cd doc
```

```console
$ make watch
```

If you're not source'd via `poetry shell`, you can use this:

```console
$ make SPHINXBUILD='poetry run sphinx-build' watch
```

(tmuxp-developer-config)=

## tmuxp developer config

```{image} _static/tmuxp-dev-screenshot.png
:align: center

```

After you {ref}`install-dev-env`, when inside the tmuxp checkout:

```console
$ tmuxp load .
```

this will load the `.tmuxp.yaml` in the root of the project.

```{literalinclude} ../.tmuxp.yaml
:language: yaml

```

## Formatting

The project uses [black] and [isort] (one after the other). Configurations are in `pyproject.toml`
and `setup.cfg`:

- `make black isort`: Run `black` first, then `isort` to handle import nuances

## Linting

[flake8] and [mypy] run via CI in our GitHub Actions. See the configuration in `pyproject.toml` and
`setup.cfg`.

### flake8

[flake8] provides fast, reliable, barebones styling and linting.

````{tab} Command

poetry:

```console
$ poetry run flake8
```

If you setup manually:

```console
$ flake8
```

````

````{tab} make

```console
$ make flake8
```

````

````{tab} Watch

```console
$ make watch_flake8
```

requires [`entr(1)`].

````

````{tab} Configuration

See `[flake8]` in setup.cfg.

```{literalinclude} ../setup.cfg
:language: ini
:start-at: "[flake8]"
:end-before: "[isort]"

```

````

### mypy

[mypy] is used for static type checking.

````{tab} Command

poetry:

```console
$ poetry run mypy .
```

If you setup manually:

```console
$ mypy .
```

````

````{tab} make

```console
$ make mypy
```

````

````{tab} Watch

```console
$ make watch_mypy
```

requires [`entr(1)`].
````

(gh-actions)=

## Continuous integration

### Github Actions

tmuxp uses [github actions] for continuous integration / automatic unit
testing.

To view the tmux and python versions tested see the [.github/workflows/tests.yml].
Builds are done on `master` and pull requests and can be viewed on
the [gh build site].

[py.test usage argument]: https://pytest.org/latest/usage.html
[entr]: http://entrproject.org/
[`entr(1)`]: http://entrproject.org/
[black]: https://github.com/psf/black
[isort]: https://pypi.org/project/isort/
[flake8]: https://flake8.pycqa.org/
[mypy]: http://mypy-lang.org/
[github actions]: https://github.com/features/actions
[gh build site]: https://github.com/tmux-python/tmuxp/actions?query=workflow%3Atests
[.github/workflows/tests.yml]: https://github.com/tmux-python/tmuxp/blob/master/.github/workflows/tests.yml
[issue on github]: https://github.com/tmux-python/tmuxp/issues
