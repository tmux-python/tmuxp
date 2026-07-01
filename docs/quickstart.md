(quickstart)=

# Quickstart

tmuxp launches a whole tmux workspace — its windows, panes, and the commands
inside them — from a single YAML or JSON file. Install it, write one file, and
{ref}`tmuxp load <cli-load>` builds the session and drops you into it. This page
takes you from nothing to a running session.

## Installation

Ensure you have at least tmux **>= 3.2** and python **>= 3.10**.

```console
$ pip install --user tmuxp
```

If you manage dependencies with [uv] inside a project environment, add tmuxp to
your lockfile instead:

```console
$ uv add tmuxp
```

To run tmuxp without installing it globally — the way you'd use [pipx] — invoke
it through [uvx]:

```console
$ uvx tmuxp
```

Upgrade to the latest release with:

```console
$ pip install --user --upgrade tmuxp
```

Within a uv-managed project, upgrade by refreshing the lockfile and syncing:

```console
$ uv lock --upgrade-package tmuxp
```

```console
$ uv sync
```

Then install {ref}`completion`.

Homebrew users can install it with:

```console
$ brew install tmuxp
```

(developmental-releases)=

### Developmental releases

New versions of tmuxp are published to [PyPI] as alpha, beta, or release
candidates. Their version carries an `a1`, `b1`, or `rc1` suffix — `1.10.0b4` is
the fourth beta of `1.10.0`, before general availability.

Install the latest pre-release with the tool you use:

```console
$ pip install --user --upgrade --pre tmuxp
```

```console
$ uv add tmuxp --prerelease allow
```

```console
$ uvx --from 'tmuxp' --prerelease allow tmuxp
```

```console
$ pipx install --suffix=@next 'tmuxp' --pip-args '\--pre' --force
```

After the pipx install, load with `tmuxp@next load [session]`.

Or track trunk directly (it can break):

```console
$ pip install --user -e git+https://github.com/tmux-python/tmuxp.git#egg=tmuxp
```

```console
$ uv add "tmuxp @ git+https://github.com/tmux-python/tmuxp.git@master"
```

```console
$ uvx --from "tmuxp @ git+https://github.com/tmux-python/tmuxp.git@master" tmuxp
```

```console
$ pipx install --suffix=@master 'tmuxp @ git+https://github.com/tmux-python/tmuxp.git@master' --force
```

[pip]: https://pip.pypa.io/en/stable/
[pipx]: https://pypa.github.io/pipx/docs/
[PyPI]: https://pypi.org/project/tmuxp/
[uv]: https://docs.astral.sh/uv/getting-started/features/#python-versions
[uvx]: https://docs.astral.sh/uv/guides/tools/

## Commands

:::{seealso}

{ref}`examples`, {ref}`commands`, {ref}`completion`.

:::

tmuxp launches workspaces / sessions from JSON and YAML files.

Workspace files live in `$HOME/.tmuxp`, or in a project directory as
`.tmuxp.yaml`, `.tmuxp.yml`, or `.tmuxp.json`. Every workspace file needs:

1. a `session_name`
2. a list of `windows`
3. a list of `panes` for every window

Create a file, `~/.tmuxp/example.yaml`:

```{literalinclude} ../examples/2-pane-vertical.yaml
:language: yaml
```

```console
$ tmuxp load example.yaml
```

This builds and attaches your session.

Load several at once:

```console
$ tmuxp load example.yaml anothersession.yaml
```

If you're already inside a session, tmuxp offers to `switch-client` for you, or
to append the new windows to the session you're in.

You can point tmuxp at a different config directory with the `TMUXP_CONFIGDIR`
environment variable:

```console
$ TMUXP_CONFIGDIR=$HOME/.tmuxpmoo tmuxp load cpython
```

Or set it in your `~/.bashrc` / `~/.zshrc`:

```console
$ export TMUXP_CONFIGDIR=$HOME/.yourconfigdir/tmuxp
```

You can also [import][import] configs from [teamocil] and [tmuxinator].

## Pythonics

:::{seealso}

{ref}`libtmux python API documentation <libtmux:api>` and {ref}`developing`.

:::

Under the hood, tmuxp drives tmux through
[libtmux](https://libtmux.git-pull.com/) — an
[object-relational mapper][object relational mapper] and
[abstraction layer] over `tmux(1)`'s commands. Each config concept maps to a
libtmux call:

| {ref}`libtmux Python API <libtmux:api>` | {term}`tmux(1)` equivalent |
| ------------------------------------- | -------------------------- |
| {meth}`libtmux.Server.new_session`    | `$ tmux new-session`       |
| {attr}`libtmux.Server.sessions`       | `$ tmux list-sessions`     |
| {attr}`libtmux.Session.windows`       | `$ tmux list-windows`      |
| {meth}`libtmux.Session.new_window`    | `$ tmux new-window`        |
| {attr}`libtmux.Window.panes`          | `$ tmux list-panes`        |
| {meth}`libtmux.Window.split`          | `$ tmux split-window`      |
| {meth}`libtmux.Pane.send_keys`        | `$ tmux send-keys`         |

[import]: http://tmuxp.git-pull.com/commands/#import
[tmuxinator]: https://github.com/aziz/tmuxinator
[teamocil]: https://github.com/remiprev/teamocil
[abstraction layer]: http://en.wikipedia.org/wiki/Abstraction_layer
[object relational mapper]: http://en.wikipedia.org/wiki/Object-relational_mapping
