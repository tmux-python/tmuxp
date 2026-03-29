(cli-load)=

(tmuxp-load)=

(tmuxp-load-reference)=

# tmuxp load

Load tmux sessions from workspace configuration files. This is the primary command for starting sessions from YAML or JSON configurations.

## Command

```{eval-rst}
.. argparse::
    :module: tmuxp.cli
    :func: create_parser
    :prog: tmuxp
    :path: load
```

## Basic usage

You can load your tmuxp file and attach the tmux session via a few
shorthands:

1. The directory with a `.tmuxp.{yaml,yml,json}` file in it
2. The name of the project file in your `$HOME/.tmuxp` folder
3. The direct path of the tmuxp file you want to load

Path to folder with `.tmuxp.yaml`, `.tmuxp.yml`, `.tmuxp.json`:

````{tab} Project based

Projects with a file named `.tmuxp.yaml` or `.tmuxp.json` can be loaded:

```console
// current directory
$ tmuxp load .
```

```console
$ tmuxp load ../
```

```console
$ tmuxp load path/to/folder/
```

```console
$ tmuxp load /path/to/folder/
```

````

````{tab} User based

Name of the config, assume `$HOME/.tmuxp/myconfig.yaml`:

```console
$ tmuxp load myconfig
```

Direct path to json/yaml file:

```console
$ tmuxp load ./myfile.yaml
```

```console
$ tmuxp load /abs/path/to/myfile.yaml
```

```console
$ tmuxp load ~/myfile.yaml
```

````

````{tab} Direct

Absolute and relative directory paths are supported.

```console
$ tmuxp load [filename]
```

````

## Inside sessions

If you try to load a workspace file from within a tmux session, it will ask you
if you want to load and attach to the new session, or just load detached.
You can also load a workspace file and append the windows to the current active session.

```
Already inside TMUX, switch to session? yes/no
Or (a)ppend windows in the current active session?
[y/n/a]:
```

## Options

All of these options can be preselected to skip the prompt:

- Attach / open the client after load:

  ```console
  $ tmuxp load -y config
  ```

- Detached / open in background:

  ```console
  $ tmuxp load -d config
  ```

- Append windows to existing session

  ```console
  $ tmuxp load -a config
  ```

## Loading multiple sessions

Multiple sessions can be loaded at once. The first ones will be created
without being attached. The last one will be attached if there is no
`-d` flag on the command line.

```console
$ tmuxp load [filename1] [filename2] ...
```

## Custom session name

A session name can be provided at the terminal. If multiple sessions
are created, the last session is named from the terminal.

```console
$ tmuxp load -s [new_session_name] [filename1] ...
```

## Logging

The output of the `load` command can be logged to a file for
debugging purposes. the log level can be controlled with the global
`--log-level` option (defaults to INFO).

```console
$ tmuxp load [filename] --log-file [log_filename]
```

```console
$ tmuxp --log-level [LEVEL] load [filename] --log-file [log_filename]
```

## Progress display

When loading a workspace, tmuxp shows an animated spinner with build progress. The spinner updates as windows and panes are created, giving real-time feedback during session builds.

### Presets

Five built-in presets control the spinner format:

| Preset | Format |
|--------|--------|
| `default` | `Loading workspace: {session} {bar} {progress} {window}` |
| `minimal` | `Loading workspace: {session} [{window_progress}]` |
| `window` | `Loading workspace: {session} {window_bar} {window_progress_rel}` |
| `pane` | `Loading workspace: {session} {pane_bar} {session_pane_progress}` |
| `verbose` | `Loading workspace: {session} [window {window_index} of {window_total} · pane {pane_index} of {pane_total}] {window}` |

Select a preset with `--progress-format`:

```console
$ tmuxp load --progress-format minimal myproject
```

Or via environment variable:

```console
$ TMUXP_PROGRESS_FORMAT=verbose tmuxp load myproject
```

### Custom format tokens

Use a custom format string with any of the available tokens:

| Token | Description |
|-------|-------------|
| `{session}` | Session name |
| `{window}` | Current window name |
| `{window_index}` | Current window number (1-based) |
| `{window_total}` | Total number of windows |
| `{window_progress}` | Window fraction (e.g. `1/3`) |
| `{window_progress_rel}` | Completed windows fraction (e.g. `1/3`) |
| `{windows_done}` | Number of completed windows |
| `{windows_remaining}` | Number of remaining windows |
| `{pane_index}` | Current pane number in the window |
| `{pane_total}` | Total panes in the current window |
| `{pane_progress}` | Pane fraction (e.g. `2/4`) |
| `{progress}` | Combined progress (e.g. `1/3 win · 2/4 pane`) |
| `{session_pane_progress}` | Panes completed across the session (e.g. `5/10`) |
| `{overall_percent}` | Pane-based completion percentage (0–100) |
| `{bar}` | Composite progress bar |
| `{pane_bar}` | Pane-based progress bar |
| `{window_bar}` | Window-based progress bar |
| `{status_icon}` | Status icon (⏸ during before_script) |

Example:

```console
$ tmuxp load --progress-format "{session} {bar} {overall_percent}%" myproject
```

### Panel lines

The spinner shows script output in a panel below the spinner line. Control the panel height with `--progress-lines`:

Hide the panel entirely (script output goes to stdout):

```console
$ tmuxp load --progress-lines 0 myproject
```

Show unlimited lines (capped to terminal height):

```console
$ tmuxp load --progress-lines -1 myproject
```

Set a custom height (default is 3):

```console
$ tmuxp load --progress-lines 5 myproject
```

### Disabling progress

Disable the animated spinner entirely:

```console
$ tmuxp load --no-progress myproject
```

Or via environment variable:

```console
$ TMUXP_PROGRESS=0 tmuxp load myproject
```

When progress is disabled, logging flows normally to the terminal and no spinner is rendered.

### Before-script behavior

During `before_script` execution, the progress bar shows a marching animation and a ⏸ status icon, indicating that tmuxp is waiting for the script to finish before continuing with pane creation.

## Here mode

The `--here` flag reuses the current tmux window instead of creating a new session. This is similar to teamocil's `--here` flag.

```console
$ tmuxp load --here .
```

When used, tmuxp builds the workspace panes inside the current window rather than spawning a new session.

`--here` only supports a single workspace file per invocation.

```{note}
When `--here` needs to provision a directory, environment, or shell, tmuxp uses tmux primitives (`set-environment` and `respawn-pane`) instead of typing `cd` / `export` into the pane. If provisioning is needed, tmux will replace the active pane process before the workspace commands run, so long-running child processes in that pane can be terminated.
```

## Skipping shell_command_before

The `--no-shell-command-before` flag skips all `shell_command_before` entries at every level (session, window, pane). This is useful for quick reloads when the setup commands (virtualenv activation, etc.) are already active.

```console
$ tmuxp load --no-shell-command-before myproject
```

```{note}
This flag is intentionally broader than tmuxinator's `--no-pre-window`, which only disables the window-level `pre_window` chain. tmuxp's flag strips `shell_command_before` at all levels for a clean reload experience.
```

## Debug mode

The `--debug` flag shows tmux commands as they execute. This disables the progress spinner and attaches a debug handler to libtmux's logger, printing each tmux command to stdout.

```console
$ tmuxp load --debug myproject
```

## Config templating

Workspace configs support simple `{{ variable }}` placeholders for variable substitution. Pass values via `--set KEY=VALUE`:

```console
$ tmuxp load --set project=myapp mytemplate.yaml
```

Multiple variables can be passed:

```console
$ tmuxp load --set project=myapp --set env=staging mytemplate.yaml
```

In the config file, use double-brace syntax:

```yaml
session_name: "{{ project }}"
windows:
  - window_name: "{{ project }}-main"
    panes:
      - echo "Working on {{ project }}"
```

```{note}
Values containing `{{ }}` must be quoted in YAML to avoid parse errors.
```
