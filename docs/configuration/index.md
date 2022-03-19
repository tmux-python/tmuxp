(config)=

(configuration)=

# Configuration

tmuxp loads your terminal workspace into tmux using config files.

The configuration file can be JSON or YAML. It's declarative style resembles tmux's object hierarchy: session, window and wanes.

## Launching your session

Once you have `tmuxp` installed alongside tmux, you can load a workspace with:

```console
$ tmuxp load ./path/to/file
```

tmuxp will offers to assist when:

- _Session already exists_: tmuxp will prompt you to re-attach. It does this
  by checking if the configuration's `session_name` matches a session already
  running on the same server.
- _When inside a tmux client_, `tmuxp` will let you create a new session and switch to it, or append the windows to your existing
  session.

## What's in a config file?

1. A session name
2. A list of _windows_
3. A list of _panes_ for each window
4. A list of _commands_ for each pane

````{tab} Basics

```yaml
session_name: My session
windows:
- window_name: Window 1
  panes:
  - shell_command:
    - cmd: echo "pane 1"
  - shell_command:
    - cmd: echo "pane 2"
```

````

````{tab} Smallest possible

```{literalinclude} ../../examples/minimal.yaml
:language: yaml

```

As of 1.11.x.

````

Breaking down the basic configuration into sections:

1. A session name

   ```yaml
   session_name: My session
   ```

2. A list of _windows_

   ```yaml
   windows:
     - window_name: Window 1
       panes: ...
       # window settings
     - window_name: Window 2
       panes: ...
       # window settings
   ```

3. A list of _panes_ for each window

   ```yaml
   windows:
     panes:
       -  # pane settings
       -  # pane settings
   ```

4. A list of _commands_ for each pane

   ```yaml
   windows:
     panes:
       - shell_command:
           - cmd: echo "pane 1 - cmd 1"
             # command options
           - cmd: echo "pane 1 - cmd 2"
             # command options
   ```

## Where do I store config files?

### Direct

You can create a configuration and load it from anywhere in your file system.

```console
$ tmuxp load [config_file]
```

````{tab} Relative
```console
$ tmuxp load ./favorites.yaml
```
````

````{tab} Absolute
```console
$ tmuxp load /opt/myapp/favorites.yaml
```
````

### User-based configurations

tmuxp uses the [XDG Base Directory] specification.

Often on POSIX machines, you will store them in `~/.config/tmuxp`.

Assume you store `apple.yaml` in `$XDG_CONFIG_HOME/tmuxp/apple.yaml`, you can
then use:

```console
$ tmuxp load apple
```

:::{seealso}

This path can be overridden by {ref}`TMUXP_CONFIGDIR`

:::

[xdg base directory]: https://specifications.freedesktop.org/basedir-spec/latest/

### Project-specific

You can store a configuration in your project's root directory as `.tmuxp.yaml` or `.tmuxp.json`, then:

Assume `.tmuxp.yaml` inside `/opt/myapp`

```console
$ tmuxp load [config_path]
```

````{tab} In project root
```console
$ tmuxp load ./
```
````

````{tab} Absolute
```console
$ tmuxp load /opt/myapp
```
````

## Reference and usage

```{toctree}

top-level
environmental-variables
examples

```
