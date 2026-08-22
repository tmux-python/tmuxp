Output docs/_static/demos/vhs/tmuxp-load.gif
Output docs/_static/demos/vhs/tmuxp-load.mp4
Output docs/_static/demos/vhs/tmuxp-load.webm

Set Shell "bash"
Set FontSize 18
Set Theme "Catppuccin Mocha"
Set TypingSpeed 50ms
Set Padding 20
Set Width 1360
Set Height 760

# Wait syncs to the prompt returning. It only applies after the detach below;
# while attached the prompt is gone, so the attached stretch uses Sleep.
Set WaitPattern /[$#>]\s*$/
Set WaitTimeout 90s

# The sandbox from docs/_static/demos/setup-sandbox.sh. Redirecting HOME,
# XDG_CONFIG_HOME, and TMUX_TMPDIR keeps real paths off screen and runs tmux on
# an isolated server; SHELL=bash gives the session's panes a clean prompt.
Env HOME "/tmp/tmuxp-demo"
Env XDG_CONFIG_HOME "/tmp/tmuxp-demo/.config"
Env TMUX_TMPDIR "/tmp/tmuxp-demo/tmux"
Env PATH "/tmp/tmuxp-demo/bin:/usr/local/bin:/usr/bin:/bin"
Env SHELL "/bin/bash"

Hide
Type "cd ~ && tmux kill-server 2>/dev/null; clear"
Enter
Show

# No -d: tmuxp builds the session and attaches, so the recording shows the
# windows and panes come up. Watch the live server log, then detach (prefix + d)
# to end back at the shell.
Type "tmuxp load web-dev"
Enter
Sleep 7s
Ctrl+b
Sleep 500ms
Type "d"
Wait
Sleep 2s
