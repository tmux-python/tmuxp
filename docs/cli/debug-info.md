(cli-debug-info)=

(tmuxp-debug-info)=

# tmuxp debug-info

Collect and display system information useful for debugging tmuxp issues and submitting bug reports.

```{image} ../_static/demos/asciinema/tmuxp-debug-info.gif
:alt: tmuxp debug-info printing environment and version diagnostics
:width: 100%
:loading: lazy
```

## Command

```{eval-rst}
.. argparse::
    :module: tmuxp.cli
    :func: create_parser
    :prog: tmuxp
    :path: debug-info
```

## Example output

```console

$ tmuxp debug-info
--------------------------
environment:
    system: Linux
    arch: x86_64
...

```
