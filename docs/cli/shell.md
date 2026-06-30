(cli-shell)=

(tmuxp-shell)=

# tmuxp shell

Launch an interactive Python shell with [libtmux] objects pre-loaded. Like
Django's `shell` command, it hands you the current tmux server, sessions,
windows, and panes already wired up, so you can poke at a live session or
prototype a script without writing boilerplate.

## Command

```{eval-rst}
.. argparse::
    :module: tmuxp.cli
    :func: create_parser
    :prog: tmuxp
    :path: shell
```

## Interactive usage

Run `tmuxp shell` to drop into a Python console with the current tmux
{class}`server <libtmux.Server>`, {class}`session <libtmux.Session>`,
{class}`window <libtmux.Window>`, and {class}`pane <libtmux.Pane>` already bound.
Pass arguments to select a specific one:

```console
(Pdb) server
<libtmux.server.Server object at 0x7f7dc8e69d10>
(Pdb) server.sessions
[Session($1 your_project)]
(Pdb) session
Session($1 your_project)
(Pdb) session.name
'your_project'
(Pdb) window
Window(@3 1:your_window, Session($1 your_project))
(Pdb) window.name
'your_window'
(Pdb) window.panes
[Pane(%6 Window(@3 1:your_window, Session($1 your_project)))
(Pdb) pane
Pane(%6 Window(@3 1:your_window, Session($1 your_project)))
```

## Running code directly

Pass `-c` to run a snippet and exit, much like `python -c`:

```console
$ tmuxp shell -c 'python code'
```

```{image} ../_static/tmuxp-shell.gif
:width: 878
:height: 109
:loading: lazy
```

The same objects are in scope. Name a server, then a window, to narrow what the
snippet sees:

```console
$ tmuxp shell -c 'print(session.name); print(window.name)'
my_server
my_window
```

```console
$ tmuxp shell my_server my_window -c 'print(window.name.upper())'
MY_WINDOW
```

Inside a tmux pane — or attached to the default server — the pane is in scope
too:

```console
$ tmuxp shell -c 'print(pane.id); print(pane.window.name)'
%2
my_window
```

## Debugger integration

`tmuxp shell` supports [PEP 553][pep 553]'s `PYTHONBREAKPOINT` and compatible
debuggers, such as [ipdb][ipdb]:

```console
$ pip install --user ipdb
```

Inside a [uv](https://docs.astral.sh/uv/getting-started/features/#python-versions)-managed
project, add `ipdb` as a development dependency:

```console
$ uv add --dev ipdb
```

For a pipx-style ad hoc install, run it through [uvx](https://docs.astral.sh/uv/guides/tools/):

```console
$ uvx --from ipdb ipdb3 --help
```

```console
$ env PYTHONBREAKPOINT=ipdb.set_trace tmuxp shell
```

## Shell detection

`tmuxp shell` drops into the richest shell available in your _site packages_. Pick
one yourself with a flag:

- `--pdb`: plain {func}`breakpoint` (python 3.7+) or {func}`pdb.set_trace`
- `--code`: drop into {func}`code.interact`, accepts `--use-pythonrc`
- `--bpython`: drop into bpython
- `--ipython`: drop into ipython
- `--ptpython`: drop into ptpython, accepts `--use-vi-mode`
- `--ptipython`: drop into ipython + ptpython, accepts `--use-vi-mode`

[pep 553]: https://www.python.org/dev/peps/pep-0553/
[ipdb]: https://pypi.org/project/ipdb/
[libtmux]: https://libtmux.git-pull.com
