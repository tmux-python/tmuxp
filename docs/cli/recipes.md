(cli-recipes)=

# Recipes

Copy-pasteable command invocations for common tasks.

## Load a workspace

```console
$ tmuxp load my-workspace.yaml
```

## Load in detached mode

```console
$ tmuxp load -d my-workspace.yaml
```

## Load from a project directory

```console
$ tmuxp load .
```

## Freeze a running session

```console
$ tmuxp freeze my-session
```

## Convert YAML to JSON

```console
$ tmuxp convert my-workspace.yaml
```

## Convert JSON to YAML

```console
$ tmuxp convert my-workspace.json
```

## List available workspaces

```console
$ tmuxp ls
```

## Search workspaces

```console
$ tmuxp search my-project
```

## Edit a workspace config

```console
$ tmuxp edit my-workspace
```

## Collect debug info

```console
$ tmuxp debug-info
```

## Shell with tmux context

```console
$ tmuxp shell
```

Access libtmux objects directly:

```console
$ tmuxp shell --best --command 'print(server.sessions)'
```
