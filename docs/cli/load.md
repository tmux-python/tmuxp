(cli-load)=

(tmuxp-load)=

# tmuxp load

You can load your tmuxp file and attach the vim session via a few
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

If you try to load a config file from within a tmux session, it will ask you
if you want to load and attach to the new session, or just load detached.
You can also load a config file and append the windows to the current active session.

```
Already inside TMUX, switch to session? yes/no
Or (a)ppend windows in the current active session?
[y/n/a]:
```

## Options

All of these options can be preselected to skip the prompt:

- Attach / open client after load:

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

## Reference

(tmuxp-load-reference)=

```{eval-rst}
.. click:: tmuxp.cli.load:command_load
    :prog: tmuxp load
    :commands: load
    :nested: full
```
