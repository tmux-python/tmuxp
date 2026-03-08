(environmental-variables)=

# Environmental variables

(TMUXP_CONFIGDIR)=

## `TMUXP_CONFIGDIR`

Example: `TMUXP_CONFIGDIR=$HOME/.mytmuxpconfigdir tmuxp load cpython`

(LIBTMUX_TMUX_FORMAT_SEPARATOR)=

## `LIBTMUX_TMUX_FORMAT_SEPARATOR`

:::{seealso}

[`LIBTMUX_TMUX_FORMAT_SEPARATOR`](https://libtmux.git-pull.com/api.html#tmux-format-separator) in libtmux API.

:::

In rare circumstances the `tmux -F` separator under the hood may cause issues
building sessions. For this case you can override it here.

```console
$ env LIBTMUX_TMUX_FORMAT_SEPARATOR='__SEP__' tmuxp load [session]
```

(TMUXP_PROGRESS)=

## `TMUXP_PROGRESS`

Master on/off switch for the animated progress spinner during `tmuxp load`.
Defaults to `1` (enabled). Set to `0` to disable:

```console
$ TMUXP_PROGRESS=0 tmuxp load myproject
```

Equivalent to the `--no-progress` CLI flag.

(TMUXP_PROGRESS_FORMAT)=

## `TMUXP_PROGRESS_FORMAT`

Set the spinner line format. Accepts a preset name (`default`, `minimal`, `window`, `pane`, `verbose`) or a custom format string with tokens like `{session}`, `{bar}`, `{progress}`:

```console
$ TMUXP_PROGRESS_FORMAT=minimal tmuxp load myproject
```

Custom format example:

```console
$ TMUXP_PROGRESS_FORMAT="{session} {bar} {overall_percent}%" tmuxp load myproject
```

Equivalent to the `--progress-format` CLI flag.

(TMUXP_PROGRESS_LINES)=

## `TMUXP_PROGRESS_LINES`

Number of script-output lines shown in the spinner panel. Defaults to `3`.

Set to `0` to hide the panel entirely (script output goes to stdout):

```console
$ TMUXP_PROGRESS_LINES=0 tmuxp load myproject
```

Set to `-1` for unlimited lines (capped to terminal height):

```console
$ TMUXP_PROGRESS_LINES=-1 tmuxp load myproject
```

Equivalent to the `--progress-lines` CLI flag.
