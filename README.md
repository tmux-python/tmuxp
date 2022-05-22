# tmuxp

A session manager for tmux. Built on [libtmux](https://github.com/tmux-python/libtmux).

[![Python Package](https://img.shields.io/pypi/v/tmuxp.svg)](https://pypi.org/project/tmuxp/)
[![Docs](https://github.com/tmux-python/tmuxp/workflows/docs/badge.svg)](https://tmuxp.git-pull.com/)
[![Build status](https://github.com/tmux-python/tmuxp/workflows/tests/badge.svg)](https://github.com/tmux-python/tmuxp/actions?query=workflow%3A%22tests%22)
[![Code Coverage](https://codecov.io/gh/tmux-python/tmuxp/branch/master/graph/badge.svg)](https://codecov.io/gh/tmux-python/tmuxp)
[![License](https://img.shields.io/github/license/tmux-python/tmuxp.svg)](https://github.com/tmux-python/tmuxp/blob/master/LICENSE)

**New to tmux?** [The Tao of tmux](https://leanpub.com/the-tao-of-tmux)
is available on Leanpub and [Amazon Kindle](http://amzn.to/2gPfRhC).
Read and browse the book for free [on the
web](https://leanpub.com/the-tao-of-tmux/read).

**Have some spare time?** Help us triage and code review and the tracker. See [issue
#290](https://github.com/tmux-python/tmuxp/discussions/290)!

# Installation

pip:

```console
$ pip install --user tmuxp
```

Homebrew:

```console
$ brew install tmuxp
```

Debian / ubuntu:

```console
$ sudo apt install tmuxp
```

Find the package for your distro on repology: <https://repology.org/project/tmuxp/versions>

Developmental releases:

- [pip](https://pip.pypa.io/en/stable/):

  ```console
  $ pip install --user --upgrade --pre tmuxp
  ```

- [pipx](https://pypa.github.io/pipx/docs/):

  ```console
  $ pipx install --suffix=@next 'tmuxp' --pip-args '\--pre' --force
  ```

  Then use `tmuxp@next load [session]`.

# Load a tmux session

Load tmux sessions via json and YAML,
[tmuxinator](https://github.com/aziz/tmuxinator) and
[teamocil](https://github.com/remiprev/teamocil) style.

```yaml
session_name: 4-pane-split
windows:
  - window_name: dev window
    layout: tiled
    shell_command_before:
      - cd ~/ # run as a first command in all panes
    panes:
      - shell_command: # pane no. 1
          - cd /var/log # run multiple commands in this pane
          - ls -al | grep \.log
      - echo second pane # pane no. 2
      - echo third pane # pane no. 3
      - echo forth pane # pane no. 4
```

Save as _mysession.yaml_, and load:

```console
$ tmuxp load ./mysession.yaml
```

Projects with _.tmuxp.yaml_ or _.tmuxp.json_ load via directory:

```console
$ tmuxp load path/to/my/project/
```

Load multiple at once (in bg, offer to attach last):

```console
$ tmuxp load mysession ./another/project/
```

Name a session:

```console
$ tmuxp load -s session_name ./mysession.yaml
```

[simple](http://tmuxp.git-pull.com/examples.html#short-hand-inline) and
[very
elaborate](http://tmuxp.git-pull.com/examples.html#super-advanced-dev-environment)
config examples

# User-level configurations

tmuxp checks for configs in user directories:

- `$TMUXP_CONFIGDIR`, if set
- `$XDG_CONFIG_HOME`, usually _$HOME/.config/tmuxp/_
- `$HOME/.tmuxp/`

Load your tmuxp config from anywhere by using the filename, assuming
_\~/.config/tmuxp/mysession.yaml_ (or _.json_):

```console
$ tmuxp load mysession
```

See [author's tmuxp configs](https://github.com/tony/tmuxp-config) and
the projects'
[tmuxp.yaml](https://github.com/tmux-python/tmuxp/blob/master/.tmuxp.yaml).

# Shell

_New in 1.6.0_:

`tmuxp shell` launches into a python console preloaded with the attached
server, session, and window in
[libtmux](https://github.com/tmux-python/libtmux) objects.

```console
$ tmuxp shell

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
Pane(%6 Window(@3 1:your_window, Session($1 your_project))
```

Python 3.7+ supports [PEP
553](https://www.python.org/dev/peps/pep-0553/) `breakpoint()`
(including `PYTHONBREAKPOINT`). Also supports direct commands via `-c`:

```console
$ tmuxp shell -c 'print(window.name)'
my_window

$ tmuxp shell -c 'print(window.name.upper())'
MY_WINDOW
```

Read more on [tmuxp shell](https://tmuxp.git-pull.com/cli/shell.html) in
the CLI docs.

# Pre-load hook

Run custom startup scripts (such as installing project dependencies
before loading tmux. See the
[bootstrap_env.py](https://github.com/tmux-python/tmuxp/blob/master/bootstrap_env.py)
and
[before_script](http://tmuxp.git-pull.com/examples.html#bootstrap-project-before-launch)
example

# Load in detached state

You can also load sessions in the background by passing `-d` flag

# Screenshot

<img src="https://raw.githubusercontent.com/tmux-python/tmuxp/master/docs/_static/tmuxp-demo.gif" class="align-center" style="width:45.0%" alt="image" />

# Freeze a tmux session

Snapshot your tmux layout, pane paths, and window/session names.

```console
$ tmuxp freeze session-name
```

See more about [freezing
tmux](http://tmuxp.git-pull.com/commands/#freeze-sessions) sessions.

# Convert a session file

Convert a session file from yaml to json and vice versa.

```console
$ tmuxp convert filename
```

This will prompt you for confirmation and shows you the new file that is
going to be written.

You can auto confirm the prompt. In this case no preview will be shown.

```console
$ tmuxp convert -y filename
$ tmuxp convert --yes filename
```

# Plugin System

tmuxp has a plugin system to allow for custom behavior. See more about
the [Plugin System](http://tmuxp.git-pull.com/plugin_system.html).

# Debugging Helpers

The `load` command provides a way to log output to a log file for
debugging purposes.

```console
$ tmuxp load --log-file <log-file-name> .
```

Collect system info to submit with a Github issue:

```console
$ tmuxp debug-info
------------------
environment:
    system: Linux
    arch: x86_64

# ... so on
```

# Docs / Reading material

See the [Quickstart](http://tmuxp.git-pull.com/quickstart.html).

[Documentation](http://tmuxp.git-pull.com) homepage (also in
[中文](http://tmuxp-zh.rtfd.org/))

Want to learn more about tmux itself? [Read The Tao of Tmux
online](http://tmuxp.git-pull.com/about_tmux.html).

# Donations

Your donations fund development of new features, testing and support.
Your money will go directly to maintenance and development of the
project. If you are an individual, feel free to give whatever feels
right for the value you get out of the project.

See donation options at <https://git-pull.com/support.html>.

# Project details

- tmux support: 1.8+
- python support: >= 3.7, pypy, pypy3
- Source: <https://github.com/tmux-python/tmuxp>
- Docs: <https://tmuxp.git-pull.com>
- API: <https://tmuxp.git-pull.com/api.html>
- Changelog: <https://tmuxp.git-pull.com/history.html>
- Issues: <https://github.com/tmux-python/tmuxp/issues>
- Test Coverage: <https://codecov.io/gh/tmux-python/tmuxp>
- pypi: <https://pypi.python.org/pypi/tmuxp>
- Open Hub: <https://www.openhub.net/p/tmuxp-python>
- Repology: <https://repology.org/project/tmuxp/versions>
- License: [MIT](http://opensource.org/licenses/MIT).
