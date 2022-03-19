(config)=

(configuration)=

# Configuration

The configuration syntax is declarative and based on tmux's Session, Window and
Panes hierarchy. Both JSON and YAML is accepted.

## Launching your session

When you have `tmuxp` installed in your environment alongside tmux, you can use:

```console
$ tmuxp load ./path/to/file
```

to load your workspace and launch directly into tmux.

In certain cases, tmuxp will try help you when:

- _If your session already exists_: tmuxp will prompt you to re-attach. It does this
  by checking if the configuration's `session_name` matches a session already
  running on the same server.
- _If you're inside a tmux client already_, `tmuxp` will let you create a new session and switch to it, or append the windows to your existing
  session.

## What's in a config?

1. A session name: `session_name: your session`
2. A list of _windows_
3. A list of _panes_ for each window
4. A list of _commands_ for each pane

````{tab} Basics

```yaml
session_name: My session
windows:
- window_name: Window 1
  panes:
  - echo "pane 1"
  - echo "pane 2"
```

````

````{tab} Smallest possible

```{literalinclude} ../../examples/minimal.yaml
:language: yaml

```

As of 1.11.x.

````

## Reference and usage

```{toctree}

environmental-variables
examples

```
