(loading-workspaces)=

# Loading workspaces

When you run `tmuxp load`, tmuxp creates the tmux session described by your
workspace file, waits for panes to be ready, then finishes each window by
applying layouts and sending commands.

## What happens during load

tmuxp loads a workspace in two broad phases.

First, tmuxp creates the session structure. It creates each configured window
and its panes so the panes can start their shells in parallel.

Then, tmuxp waits for the panes to be ready. Once the shells have drawn their
prompts, tmuxp finishes each window by applying layout, sending configured
commands, running window-level configuration, and firing
{meth}`~tmuxp.plugin.TmuxpPlugin.after_window_finished` plugin hooks.

This means {meth}`~tmuxp.plugin.TmuxpPlugin.on_window_create` runs while the
window is created, while
{meth}`~tmuxp.plugin.TmuxpPlugin.after_window_finished` runs later, after that
window has been laid out and configured.

## Reading the progress line

The default progress line reports the same build in a compact form:

```text
Loading workspace: study ▓▓░░░░░░░░ 0/2 win · pane 3/4 learning-asyncio
```

The fraction before `win` is finished windows over windows created so far. In
the example above, two windows have been created and neither has finished yet.

The `pane` fraction describes the current window's pane creation progress. When
a new window starts, this can briefly show `pane 0/N` before tmuxp creates the
first pane for that window.

The progress bar shows the whole workspace:

- `█` means a window is finished.
- `▓` means a window has been created but is not finished yet.
- `░` means a window has not been created yet.

Once tmuxp enters the finish phase, the finished-window count rises:

```text
Loading workspace: study █▓░░░░░░░░ 1/2 win learning-dsa
```

## Why tmuxp loads this way

Creating all panes before finishing windows lets shell startup happen in
parallel. The later finish phase can then apply layouts and commands after the
panes are ready, which avoids resizing panes while shells are still drawing
their first prompts.
