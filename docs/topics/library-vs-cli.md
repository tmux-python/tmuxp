# Library vs CLI

tmuxp is a CLI tool. [libtmux](https://libtmux.git-pull.com/) is the Python library it's built on. Both control tmux, but they serve different needs.

## When to Use the CLI

Use `tmuxp` when:

- You want **declarative workspace configs** — define your layout in YAML, load it with one command
- You're setting up **daily development environments** — same windows, same panes, every time
- You need **CI/CD tmux sessions** — `tmuxp load -d` in a script
- You prefer **configuration over code** — no Python needed

```console
$ tmuxp load my-workspace.yaml
```

## When to Use libtmux

Use [libtmux](https://libtmux.git-pull.com/) directly when:

- You need **dynamic logic** — conditionals, loops, branching based on state
- You want to **read pane output** — capture what's on screen and react to it
- You're **testing** tmux interactions — libtmux provides pytest fixtures
- You need **multi-server orchestration** — manage multiple tmux servers programmatically
- The CLI's config format **can't express** what you need

```python
import libtmux

server = libtmux.Server()
session = server.new_session("my-project")
window = session.new_window("editor")
pane = window.split()
pane.send_keys("vim .")
```

## Concept Mapping

How tmuxp config keys map to libtmux API calls:

| tmuxp YAML | libtmux equivalent |
|------------|-------------------|
| `session_name: foo` | `server.new_session(session_name="foo")` |
| `windows:` | `session.new_window(...)` |
| `panes:` | `window.split(...)` |
| `shell_command:` | `pane.send_keys(...)` |
| `layout: main-vertical` | `window.select_layout("main-vertical")` |
| `start_directory: ~/project` | `session.new_window(start_directory="~/project")` |
| `before_script:` | Run via `subprocess` before building |

## What the CLI Can't Express

tmuxp configs are static declarations. They can't:

- **Branch on conditions** — "only create this pane if a file exists"
- **Read pane output** — "wait until the server is ready, then open the browser"
- **React to state** — "if this session already has 3 windows, add a 4th"
- **Orchestrate across servers** — "connect to both local and remote tmux"
- **Build layouts dynamically** — "create N panes based on a list of services"

For these, use libtmux directly. See the [libtmux quickstart](https://libtmux.git-pull.com/quickstart.html).
