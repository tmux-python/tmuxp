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
