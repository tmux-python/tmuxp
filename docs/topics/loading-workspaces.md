(loading-workspaces)=

# Loading workspaces

When you run `tmuxp load`, tmuxp creates the tmux session described by your
workspace file, waits for panes to be ready, then finishes each window by
applying layouts and sending commands.

## What happens during load

tmuxp builds each window in config order.

For each window, tmuxp creates the window and prepares its panes. When later
pane `start_directory` values already exist, panes can start their shells
together and tmuxp waits for them together.

Once the panes are ready, tmuxp applies layout, sends configured commands,
runs window-level configuration, and fires
{meth}`~tmuxp.plugin.TmuxpPlugin.after_window_finished` plugin hooks.

This means {meth}`~tmuxp.plugin.TmuxpPlugin.on_window_create` runs while the
window is created, while
{meth}`~tmuxp.plugin.TmuxpPlugin.after_window_finished` runs later, after that
window has been laid out and configured.

## Reading the progress line

The default progress line reports the same build in a compact form:

```text
Loading workspace: study ▓░░░░░░░░░ 0/1 win · pane 3/4 learning-asyncio
```

The fraction before `win` is finished windows over windows created so far. In
the example above, one window has been created and has not finished yet.

The `pane` fraction describes the current window's pane creation progress. When
a new window starts, this can briefly show `pane 0/N` before tmuxp creates the
first pane for that window.

The progress bar shows the whole workspace:

- `█` means a window is finished.
- `▓` means a window has been created but is not finished yet.
- `░` means a window has not been created yet.

Once tmuxp enters the finish phase, the finished-window count rises:

```text
Loading workspace: study █░░░░░░░░░ 1/1 win learning-asyncio
```

## Why tmuxp loads this way

Preparing a window's panes before layout lets shell startup happen in parallel
when config-order dependencies allow it. Layout and commands then run after the
panes are ready, which avoids resizing panes while shells are still drawing
their first prompts.
