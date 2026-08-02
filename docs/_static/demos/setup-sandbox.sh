#!/usr/bin/env bash
# Build the sandbox the demo tapes record against.
#
# Everything lives under /tmp/tmuxp-demo, which the tapes point HOME,
# XDG_CONFIG_HOME, and TMUX_TMPDIR at. That keeps the recordings off the real
# home directory: every path on screen renders as ~/... or /tmp/tmuxp-demo/...
# instead of a developer's actual layout, and tmux runs on an isolated server.
#
# Idempotent: wipes and rebuilds. Re-run before re-rendering any tape.
set -euo pipefail

DEMO_DIR=/tmp/tmuxp-demo

# Resolve the tmuxp under test. Defaults to this repository so the sandbox is
# self-contained and reproducible; override with TMUXP_SRC to record a
# different checkout.
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TMUXP_SRC="${TMUXP_SRC:-$(cd "$SCRIPT_DIR/../../.." && pwd)}"

rm -rf "$DEMO_DIR"
mkdir -p "$DEMO_DIR/.config/tmuxp" "$DEMO_DIR/bin" "$DEMO_DIR/tmux"

# Suppress the login-shell "message of the day" banner in the panes tmux spawns
# for the attached `load` demo, and give those panes a neutral `$ ` prompt
# instead of one that prints the sandbox user and host.
touch "$DEMO_DIR/.hushlogin"
cat > "$DEMO_DIR/.bash_profile" <<'SH'
PS1='$ '
SH

# A Solarized Dark theme for the attached `load` demo, adapted from a personal
# ~/.tmux.conf: the palette and a centered window list, but a status bar that
# shows the session name and a clock instead of the host and system load. Prefix
# is left at the default C-b so the recorded detach (prefix + d) still works.
cat > "$DEMO_DIR/.tmux.conf" <<'TMUX'
set -g status-style bg=colour235,fg=colour136,default
setw -g window-status-style fg=colour244,bg=default,dim
setw -g window-status-current-style fg=colour166,bg=default,bright
set -g pane-border-style fg=colour61
set -g pane-active-border-style fg=colour64
set -g message-style bg=colour235,fg=colour166
setw -g clock-mode-colour colour64

set -g status-interval 1
set -g status-justify centre
set -g status-left-length 24
set -g status-right-length 40
set -g status-left '#[fg=colour64,bold] #S #[default]'
set -g status-right '#[fg=colour37]%H:%M#[default] '

set -g base-index 1
TMUX

# A sandbox-local install so every path the CLI prints -- notably
# `tmuxp debug-info`, which reports its own import path -- renders under the
# sandbox venv rather than a developer's home directory.
uv venv "$DEMO_DIR/.venv" >/dev/null 2>&1
uv pip install --python "$DEMO_DIR/.venv/bin/python" "$TMUXP_SRC" >/dev/null 2>&1

# The tapes put $DEMO_DIR/bin first on PATH, so `tmuxp` resolves here without
# any absolute developer path appearing in a committed tape.
printf '#!/usr/bin/env bash\nexec %q "$@"\n' "$DEMO_DIR/.venv/bin/tmuxp" > "$DEMO_DIR/bin/tmuxp"
chmod +x "$DEMO_DIR/bin/tmuxp"

# A named command for the web-dev editor's live-log pane, so the attached demo
# reads `$ serve-log` rather than an inline while-loop.
cat > "$DEMO_DIR/bin/serve-log" <<'SH'
#!/usr/bin/env bash
while true; do printf '%s  GET /api/users  200  12ms\n' "$(date +%T)"; sleep 1; done
SH
chmod +x "$DEMO_DIR/bin/serve-log"

# ------------------------------------------------------------ workspace files
# Eight recognizable project sessions with descriptive names and varied window
# names, so `ls` shows a tidy set, `search` visibly narrows, and `load`/`freeze`
# have a real multi-window session (web-dev) to build and snapshot.
cat > "$DEMO_DIR/.config/tmuxp/web-dev.yaml" <<'YAML'
session_name: web-dev
start_directory: ~/code/webapp
windows:
  - window_name: editor
    layout: main-vertical
    focus: true
    panes:
      - focus: true
        shell_command: vim -n app.py
      - git log --oneline --graph --decorate --all -12
      - serve-log
  - window_name: server
    panes:
      - git status
  - window_name: logs
    panes:
      - htop
YAML

cat > "$DEMO_DIR/.config/tmuxp/blog.yaml" <<'YAML'
session_name: blog
windows:
  - window_name: writing
    panes:
      - vim content/post.md
  - window_name: preview
    panes:
      - hugo server -D
YAML

cat > "$DEMO_DIR/.config/tmuxp/data-science.yaml" <<'YAML'
session_name: data-science
windows:
  - window_name: notebook
    panes:
      - jupyter lab
  - window_name: analysis
    panes:
      - python analyze.py
YAML

cat > "$DEMO_DIR/.config/tmuxp/api-backend.yaml" <<'YAML'
session_name: api-backend
windows:
  - window_name: editor
    panes:
      - vim app.py
  - window_name: api
    panes:
      - flask run --debug
  - window_name: db
    panes:
      - psql app_db
YAML

cat > "$DEMO_DIR/.config/tmuxp/dotfiles.yaml" <<'YAML'
session_name: dotfiles
windows:
  - window_name: edit
    panes:
      - vim ~/.tmux.conf
YAML

cat > "$DEMO_DIR/.config/tmuxp/devops.yaml" <<'YAML'
session_name: devops
windows:
  - window_name: cluster
    panes:
      - k9s
  - window_name: logs
    panes:
      - kubectl logs -f deploy/web
YAML

cat > "$DEMO_DIR/.config/tmuxp/game-dev.yaml" <<'YAML'
session_name: game-dev
windows:
  - window_name: editor
    panes:
      - nvim main.gd
  - window_name: build
    panes:
      - godot --headless --export
YAML

cat > "$DEMO_DIR/.config/tmuxp/music-studio.yaml" <<'YAML'
session_name: music-studio
windows:
  - window_name: sequencer
    panes:
      - sonic-pi
YAML

# ------------------------------------------------------- web-dev working tree
# A small Flask repo so the web-dev session's editor pane opens a real buffer
# and its git panes show a populated log graph and a modified file on attach.
APP="$DEMO_DIR/code/webapp"
mkdir -p "$APP"
git init -q -b main "$APP"
git -C "$APP" config user.email demo@example.com
git -C "$APP" config user.name Demo

printf '# webapp\n\nA tiny demo API served with Flask.\n' > "$APP/README.md"
git -C "$APP" add -A && git -C "$APP" commit -qm "Add project README"

cat > "$APP/app.py" <<'PY'
from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/api/users")
def users():
    return jsonify([{"id": 1, "name": "ada"}, {"id": 2, "name": "grace"}])
PY
git -C "$APP" add -A && git -C "$APP" commit -qm "Serve /api/users from a Flask app"

git -C "$APP" checkout -q -b feature/health
printf 'def healthcheck():\n    return {"status": "ok"}\n' > "$APP/health.py"
git -C "$APP" add -A && git -C "$APP" commit -qm "Add healthcheck stub"
git -C "$APP" checkout -q main
printf '\nif __name__ == "__main__":\n    app.run(debug=True)\n' >> "$APP/app.py"
git -C "$APP" add -A && git -C "$APP" commit -qm "Run app under __main__"

# Leave one tracked change so git status shows a modified file on attach.
printf '\nRun with: flask --app app run\n' >> "$APP/README.md"

# ------------------------------------------------------------------- restore
# Mutative demos (convert, freeze) reset from this backup between takes.
cp -r "$DEMO_DIR/.config/tmuxp" "$DEMO_DIR/.config/tmuxp.bak"

echo "sandbox ready: $DEMO_DIR ($(ls "$DEMO_DIR/.config/tmuxp"/*.yaml | wc -l) workspaces)"
