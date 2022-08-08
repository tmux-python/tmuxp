(quickstart)=

# Quickstart

## Installation

Assure you have at least tmux **>= 1.8** and python **>= 3.7**.

```console
$ pip install --user tmuxp
```

You can upgrade to the latest release with:

```console
$ pip install --user --upgrade tmuxp
```

Then install {ref}`completion`.

If you are a Homebrew user you can install it with:

```console
$ brew install tmuxp
```

(developmental-releases)=

### Developmental releases

New versions of tmuxp are published to PyPI as alpha, beta, or release candidates.
In their versions you will see notification like `a1`, `b1`, and `rc1`, respectively.
`1.10.0b4` would mean the 4th beta release of `1.10.0` before general availability.

- [pip]\:

  ```console
  $ pip install --user --upgrade --pre tmuxp
  ```

- [pipx]\:

  ```console
  $ pipx install --suffix=@next 'tmuxp' --pip-args '\--pre' --force
  ```

  Then use `tmuxp@next load [session]`.

via trunk (can break easily):

- [pip]\:

  ```console
  $ pip install --user -e git+https://github.com/tmux-python/tmuxp.git#egg=tmuxp
  ```

- [pipx]\:

  ```console
  $ pipx install --suffix=@master 'tmuxp @ git+https://github.com/tmux-python/tmuxp.git@master' --force
  ```

[pip]: https://pip.pypa.io/en/stable/
[pipx]: https://pypa.github.io/pipx/docs/

## Commands

:::{seealso}

{ref}`examples`, {ref}`commands`, {ref}`completion`.

:::

tmuxp launches workspaces / sessions from JSON and YAML files.

Configuration files can be stored in `$HOME/.tmuxp` or in project
directories as `.tmuxp.py`, `.tmuxp.json` or `.tmuxp.yaml`.

Every configuration is required to have:

1. `session_name`
2. list of `windows`
3. list of `panes` for every window in `windows`

Create a file, `~/.tmuxp/example.yaml`:

```{literalinclude} ../examples/2-pane-vertical.yaml
:language: yaml

```

```console

$ tmuxp load example.yaml

```

This creates your tmuxp session.

Load multiple tmux sessions at once:

```console

$ tmuxp load example.yaml anothersession.yaml

```

tmuxp will offer to `switch-client` for you if you're already in a
session. You can also load a configuration, and append the windows to
the current active session.

You can also have a custom tmuxp config directory by setting the
`TMUXP_CONFIGDIR` in your environment variables.

```console

$ TMUXP_CONFIGDIR=$HOME/.tmuxpmoo tmuxp load cpython

```

Or in your `~/.bashrc` / `~/.zshrc` you can set:

```console

export TMUXP_CONFIGDIR=$HOME/.yourconfigdir/tmuxp

```

You can also [Import][import] configs [teamocil] and [tmuxinator].

## Pythonics

:::{seealso}

{ref}`libtmux python API documentation <libtmux:api>` and {ref}`developing`.

:::

ORM - [Object Relational Mapper][object relational mapper]

AL - [Abstraction Layer][abstraction layer]

### python abstraction layer

| {ref}`tmuxp python api <libtmux:api>` | {term}`tmux(1)` equivalent |
| ------------------------------------- | -------------------------- |
| {meth}`libtmux.Server.new_session`    | `$ tmux new-session`       |
| {meth}`libtmux.Server.list_sessions`  | `$ tmux list-sessions`     |
| {meth}`libtmux.Session.list_windows`  | `$ tmux list-windows`      |
| {meth}`libtmux.Session.new_window`    | `$ tmux new-window`        |
| {meth}`libtmux.Window.list_panes`     | `$ tmux list-panes`        |
| {meth}`libtmux.Window.split_window`   | `$ tmux split-window`      |
| {meth}`libtmux.Pane.send_keys`        | `$ tmux send-keys`         |

[import]: http://tmuxp.git-pull.com/commands/#import
[tmuxinator]: https://github.com/aziz/tmuxinator
[teamocil]: https://github.com/remiprev/teamocil
[abstraction layer]: http://en.wikipedia.org/wiki/Abstraction_layer
[object relational mapper]: http://en.wikipedia.org/wiki/Object-relational_mapping
