(cli-shell)=

# tmuxp shell

```{eval-rst}
.. click:: tmuxp.cli.shell:command_shell
    :prog: tmuxp shell
    :commands: shell
    :nested: none
```

## Directly enter commands

```console
$ tmuxp shell -c 'python code'
```

## Example

```{image} ../_static/tmuxp-shell.gif
:width: 100%
```

## Guide

Launch into a python console with [libtmux] objects. Compare to django's shell.

Automatically preloads current tmux {class}`server <libtmux.Server>`,
{class}`session <libtmux.Session>`, {class}`window <libtmux.Window>`
{class}`pane <libtmux.Pane>`. Pass additional arguments to select a
specific one of your choice:

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

Supports [PEP 553][pep 553]'s `PYTHONBREAKPOINT` and
compatible debuggers, for instance [ipdb][ipdb]:

```console
$ pip install --user ipdb
```

```console
$ env PYTHONBREAKPOINT=ipdb.set_trace tmuxp shell
```

You can also pass in python code directly, similar to `python -c`, do
this via `tmuxp -c`:

```console
$ tmuxp shell -c 'print(session.name); print(window.name)'
my_server
my_window
```

```console
$ tmuxp shell my_server -c 'print(session.name); print(window.name)'
my_server
my_window
```

```console
$ tmuxp shell my_server my_window -c 'print(session.name); print(window.name)'
my_server
my_window
```

```console
$ tmuxp shell my_server my_window -c 'print(window.name.upper())'
MY_WINDOW
```

Assuming inside a tmux pane or one is attached on default server:

```console
$ tmuxp shell -c 'print(pane.id); print(pane.window.name)'
%2
my_window
```

[pep 553]: https://www.python.org/dev/peps/pep-0553/
[ipdb]: https://pypi.org/project/ipdb/
[libtmux]: https://libtmux.git-pull.com

## Shell detection

`tmuxp shell` detects the richest shell available in your _site packages_, you can also pick your shell via args:

- `--pdb`: Use plain old `breakpoint()` (python 3.7+) or
  `pdb.set_trace`
- `--code`: Drop into `code.interact`, accepts `--use-pythonrc`
- `--bpython`: Drop into bpython
- `--ipython`: Drop into ipython
- `--ptpython`: Drop into ptpython, accepts `--use-vi-mode`
- `--ptipython`: Drop into ipython + ptpython, accepts
  `--use-vi-mode`
