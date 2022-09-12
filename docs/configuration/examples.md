(examples)=

# Examples

## Short hand / inline style

tmuxp has a short-hand syntax to for those who wish to keep their configs
punctual.

::::{sidebar} short hand

```{eval-rst}
.. aafig::
   :textual:

    +-------------------+
    | 'did you know'    |
    | 'you can inline'  |
    +-------------------+
    | 'single commands' |
    |                   |
    +-------------------+
    | 'for panes'       |
    |                   |
    +-------------------+
```

::::

````{tab} YAML

```{literalinclude} ../../examples/shorthands.yaml
:language: yaml

```


````

````{tab} JSON

```{literalinclude} ../../examples/shorthands.json
:language: json

```

````

## Blank panes

No need to repeat `pwd` or a dummy command. A `null`, `'blank'`,
`'pane'` are valid.

Note `''` counts as an empty carriage return.

````{tab} YAML

```{literalinclude} ../../examples/blank-panes.yaml
:language: yaml

```

````

````{tab} JSON

```{literalinclude} ../../examples/blank-panes.json
:language: json

```

````

## 2 panes

::::{sidebar} 2 pane

```{eval-rst}
.. aafig::

    +-----------------+
    | $ pwd           |
    |                 |
    |                 |
    +-----------------+
    | $ pwd           |
    |                 |
    |                 |
    +-----------------+
```

::::

````{tab} YAML

```{literalinclude} ../../examples/2-pane-vertical.yaml
:language: yaml

```

````

````{tab} JSON

```{literalinclude} ../../examples/2-pane-vertical.json
:language: json

```

````

## 3 panes

::::{sidebar} 3 panes

```{eval-rst}
.. aafig::

    +-----------------+
    | $ pwd           |
    |                 |
    |                 |
    +--------+--------+
    | $ pwd  | $ pwd  |
    |        |        |
    |        |        |
    +--------+--------+
```

::::

````{tab} YAML

```{literalinclude} ../../examples/3-pane.yaml
:language: yaml

```

````

````{tab} JSON

```{literalinclude} ../../examples/3-pane.json
:language: json

```

````

## 4 panes

::::{sidebar} 4 panes

```{eval-rst}
.. aafig::

    +--------+--------+
    | $ pwd  | $ pwd  |
    |        |        |
    |        |        |
    +--------+--------+
    | $ pwd  | $ pwd  |
    |        |        |
    |        |        |
    +--------+--------+
```

::::

````{tab} YAML

```{literalinclude} ../../examples/4-pane.yaml
:language: yaml

```

````

````{tab} JSON

```{literalinclude} ../../examples/4-pane.json
:language: json

```

````

## Start Directory

Equivalent to `tmux new-window -c <start-directory>`.

````{tab} YAML

```{literalinclude} ../../examples/start-directory.yaml
:language: yaml

```

````

````{tab} JSON

```{literalinclude} ../../examples/start-directory.json
:language: json

```

````

## Environment variable replacing

tmuxp will replace environment variables wrapped in curly brackets
for values of these settings:

- `start_directory`
- `before_script`
- `session_name`
- `window_name`
- `shell_command_before`
- `global_options`
- `options` in session scope and window scope

tmuxp replaces these variables before-hand with variables in the
terminal `tmuxp` invokes in.

In this case of this example, assuming the username "user":

```console
$ MY_ENV_VAR=foo tmuxp load examples/env-variables.yaml
```

and your session name will be `session - user (foo)`.

Shell variables in `shell_command` do not support this type of
concatenation. `shell_command` and `shell_command_before` both
support normal shell variables, since they are sent into panes
automatically via `send-key` in `tmux(1)`. See `ls $PWD` in
example.

If you have a special case and would like to see behavior changed,
please make a ticket on the [issue tracker][issue tracker].

[issue tracker]: https://github.com/tmux-python/tmuxp/issues

````{tab} YAML

```{literalinclude} ../../examples/env-variables.yaml
:language: yaml

```

````

````{tab} JSON

```{literalinclude} ../../examples/env-variables.json
:language: json

```

````

## Environment variables

tmuxp will set session environment variables.

````{tab} YAML

```{literalinclude} ../../examples/session-environment.yaml
:language: yaml

```
````

````{tab} JSON

```{literalinclude} ../../examples/session-environment.json
:language: json

```

````

## Focusing

tmuxp allows `focus: true` for assuring windows and panes are attached /
selected upon loading.

````{tab} YAML

```{literalinclude} ../../examples/focus-window-and-panes.yaml
:language: yaml

```

````

````{tab} JSON

```{literalinclude} ../../examples/focus-window-and-panes.json
:language: json

```

````

## Terminal History

tmuxp allows `suppress_history: false` to override the default command /
suppression when building the workspace.
This will add the `shell_command` to the shell history in the pane.
The suppression of the `shell_command` commands from the shell's history
occurs by prefixing the commands with a space when `suppress_history: true`.
Accordingly, this functionality depends on the shell being appropriately
configured: bash requires the shell variable `HISTCONTROL` to be set and
include either of the values `ignorespace` or `ignoreboth` (to also ignore
sequential duplicate commands), and zsh requires `setopt HIST_IGNORE_SPACE`.

````{tab} YAML

```{literalinclude} ../../examples/suppress-history.yaml
:language: yaml

```

````

````{tab} JSON

```{literalinclude} ../../examples/suppress-history.json
:language: json

```

````

(enter)=

## Skip command execution

See more at {ref}`enter`.

:::{note}

_Experimental setting_: behavior and api is subject to change until stable.

:::

```{versionadded} 1.10.0
`enter: false` option. Pane-level support.
```

Omit sending {kbd}`enter` to key commands. Equivalent to
[`send_keys(enter=False)`](libtmux.Pane.send_keys).

````{tab} YAML

```{literalinclude} ../../examples/skip-send.yaml
:language: yaml

```

````

````{tab} JSON

```{literalinclude} ../../examples/skip-send.json
:language: json

```

````

````{tab} YAML (pane-level)

```{literalinclude} ../../examples/skip-send-pane-level.yaml
:language: yaml

```

````

````{tab} JSON (pane-level)

```{literalinclude} ../../examples/skip-send-pane-level.json
:language: json

```

````

(sleep)=

## Pausing commands

:::{note}

_Experimental setting_: behavior and api is subject to change until stable.

:::

```{versionadded} 1.10.0
`sleep_before` and `sleep_after` options added. Pane and command-level support.
```

```{warning}
**Blocking.** This will delay loading as it runs synchronously for each pane as [`asyncio`](asyncio)) is not implemented yet.
```

Omit sending {kbd}`enter` to key commands. Equivalent to having
a [`time.sleep`](time.sleep) before and after [`send_keys`](libtmux.Pane.send_keys).

This is especially useful for expensive commands where the terminal needs some breathing room (virtualenv, poetry, pipenv, sourcing a configuration, launching a tui app, etc).

````{tab} Virtualenv

```{literalinclude} ../../examples/sleep-virtualenv.yaml
:language: yaml

```
````

````{tab} YAML

```{literalinclude} ../../examples/sleep.yaml
:language: yaml

```

````

````{tab} JSON

```{literalinclude} ../../examples/sleep.json
:language: json

```

````

````{tab} YAML (pane-level)

```{literalinclude} ../../examples/sleep-pane-level.yaml
:language: yaml

```

````

````{tab} JSON (pane-level)

```{literalinclude} ../../examples/sleep-pane-level.json
:language: json

```

````

## Window Index

You can specify a window's index using the `window_index` property. Windows
without `window_index` will use the lowest available window index.

````{tab} YAML

```{literalinclude} ../../examples/window-index.yaml
:language: yaml

```

````

````{tab} JSON

```{literalinclude} ../../examples/window-index.json
:language: json

```

````

## Shell per pane

Every pane can have its own shell or application started. This allows for usage
of the `remain-on-exit` setting to be used properly, but also to have
different shells on different panes.

````{tab} YAML

```{literalinclude} ../../examples/pane-shell.yaml
:language: yaml

```

````

````{tab} JSON

```{literalinclude} ../../examples/pane-shell.json
:language: json

```

````

## Set tmux options

Works with global (server-wide) options, session options
and window options.

Including `automatic-rename`, `default-shell`,
`default-command`, etc.

````{tab} YAML

```{literalinclude} ../../examples/options.yaml
:language: yaml

```
````

````{tab} JSON
```{literalinclude} ../../examples/options.json
:language: json

```
````

## Set window options after pane creation

Apply window options after panes have been created. Useful for
`synchronize-panes` option after executing individual commands in each
pane during creation.

````{tab} YAML
```{literalinclude} ../../examples/2-pane-synchronized.yaml
:language: yaml

```
````

````{tab} JSON
```{literalinclude} ../../examples/2-pane-synchronized.json
:language: json

```
````

## Main pane height

````{tab} YAML
```{literalinclude} ../../examples/main-pane-height.yaml
:language: yaml

```
````

````{tab} JSON
```{literalinclude} ../../examples/main-pane-height.json
:language: json

```
````

## Super-advanced dev environment

:::{seealso}

{ref}`tmuxp-developer-config` in the {ref}`developing` section.

:::

````{tab} YAML
```{literalinclude} ../../.tmuxp.yaml
:language: yaml

```
````

````{tab} JSON
```{literalinclude} ../../.tmuxp.json
:language: json

```
````

## Multi-line commands

You can use YAML's multiline syntax to easily split multiple
commands into the same shell command: https://stackoverflow.com/a/21699210

````{tab} YAML
```yaml
session_name: my project
shell_command_before:
- >
  [ -d `.venv/bin/activate` ] &&
  source .venv/bin/activate &&
  reset
- sleep 1
windows:
- window_name: first window
  layout: main-horizontal
  focus: true
  panes:
  - focus: True
  - blank
  - >
    poetry run ./manage.py migrate &&
    npm -C js run start
  - poetry run ./manage.py runserver
  options:
    main-pane-height: 35
```
````

## Bootstrap project before launch

You can use `before_script` to run a script before the tmux session
starts building. This can be used to start a script to create a virtualenv
or download a virtualenv/rbenv/package.json's dependency files before
tmuxp even begins building the session.

It works by using the [Exit Status][exit status] code returned by a script. Your
script can be any type, including bash, python, ruby, etc.

A successful script will exit with a status of `0`.

Important: the script file must be chmod executable `+x` or `755`.

Run a python script (and check for it's return code), the script is
_relative to the `.tmuxp.yaml`'s root_ (Windows and panes omitted in
this example):

````{tab} YAML
```yaml
session_name: my session
before_script: ./bootstrap.py
# ... the rest of your config

```
````

````{tab} JSON
```json
{
    "session_name": "my session",
    "before_script": "./bootstrap.py"
}

```
````

Run a shell script + check for return code on an absolute path. (Windows
and panes omitted in this example)

````{tab} YAML

```yaml
session_name: another example
before_script: /absolute/path/this.sh # abs path to shell script
# ... the rest of your config

```
````

````{tab} JSON

```json
{
    "session_name": "my session",
    "before_script": "/absolute/path/this.sh"
}

```
````

[exit status]: http://tldp.org/LDP/abs/html/exit-status.html

## Per-project tmux config

You can load your software project in tmux by placing a `.tmuxp.yaml` or
`.tmuxp.json` in the project's config and loading it.

tmuxp supports loading configs via absolute filename with `tmuxp load`
and via `$ tmuxp load .` if config is in directory.

```console

$ tmuxp load ~/workspaces/myproject.yaml

```

See examples of `tmuxp` in the wild. Have a project config to show off?
Edit this page.

- <https://github.com/tony/dockerfiles/blob/master/.tmuxp.yaml>
- <https://github.com/tony/vcspull/blob/master/.tmuxp.yaml>
- <https://github.com/tony/sphinxcontrib-github/blob/master/.tmuxp.yaml>

You can use `start_directory: ./` to make the directories relative to
the config file / project root.

## Bonus: pipenv auto-bootstrapping

:::{versionadded} 1.3.4

`before_script` CWD's into the root (session)-level
`start_directory`.

:::

If you use [pipenv][pipenv] / [poetry][poetry], you can use a script like this to ensure
your packages are installed:

````{tab} YAML

```yaml
# assuming your .tmuxp.yaml is in your project root directory
session_name: my pipenv project
start_directory: ./
before_script: pipenv install --dev --skip-lock # ensure dev deps install
windows:
- window_name: django project
  focus: true
  panes:
  - blank
  - pipenv run ./manage.py runserver

```
````

You can also source yourself into the virtual environment using
`shell_command_before`:

````{tab} YAML

```yaml
# assuming your .tmuxp.yaml is in your project root directory
session_name: my pipenv project
start_directory: ./
before_script: pipenv install --dev --skip-lock # ensure dev deps install
shell_command_before:
- '[ -d `pipenv --venv` ] && source `pipenv --venv`/bin/activate && reset'
windows:
- window_name: django project
  focus: true
  panes:
  - blank
  - ./manage.py runserver

```
````

[pipenv]: https://docs.pipenv.org/
[poetry]: https://python-poetry.org/

## Kung fu

:::{note}

tmuxp sessions can be scripted in python. The first way is to use the
ORM in the {ref}`API`. The second is to pass a {py:obj}`dict` into
{class}`~tmuxp.workspacebuilder.WorkspaceBuilder` with a correct schema.
See: {meth}`tmuxp.config.validate_schema`.

:::

Add yours? Submit a pull request to the [github][github] site!

[github]: https://github.com/tmux-python/tmuxp
