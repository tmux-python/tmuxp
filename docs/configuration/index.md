(config)=

(configuration)=

# Configuration

The configuration syntax is declarative and based on tmux's Session, Window and
Panes hierarchy. Both JSON and YAML is accepted.

## Launching your session

When you have `tmuxp` installed in your environment alongside tmux, you can load
a workspace with:

```console
$ tmuxp load ./path/to/file
```

tmuxp will offers to assist when:

- _Session already exists_: tmuxp will prompt you to re-attach. It does this
  by checking if the configuration's `session_name` matches a session already
  running on the same server.
- _When inside a tmux client_, `tmuxp` will let you create a new session and switch to it, or append the windows to your existing
  session.

## What's in a config?

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
  - shell_commands:
    - cmd: echo "pane 1"
  - shell_commands:
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
     - # pane settings
     - # pane settings
   ```
4. A list of _commands_ for each pane

   ```yaml
   windows:
     panes:
     - shell_commands:
       - cmd: echo "pane 1 - cmd 1"
         # command options
       - cmd: echo "pane 1 - cmd 2"
         # command options
   ```

## Reference and usage

```{toctree}

environmental-variables
examples

```
