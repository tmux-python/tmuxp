(top-level)=
(top-level-config)=

# Top-level configuration

## `session_name`

Used for:

- tmux session name
- checking for existing sessions

Notes:

- Session names may differ from config filename.

  e.g. _apple.yaml_:

  ```yaml
  session_name: banana
  windows:
    - panes:
        -
  ```

  Load detached:

  ```console
  $ tmuxp load ./apple.yaml -d
  ```

  Above:

  - tmuxp loads a file named _apple.yaml_ from the current directory.
  - tmuxp built a tmux session called _banana_.
  - `-d` means _detached_, loading in background.

  ```console
  $ tmux attach -t banana
  ```

  Above: Use `tmux` directly to attach _banana_.
