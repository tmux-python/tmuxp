Output docs/_static/demos/vhs/tmuxp-import.gif
Output docs/_static/demos/vhs/tmuxp-import.mp4
Output docs/_static/demos/vhs/tmuxp-import.webm

Set Shell "bash"
Set FontSize 18
Set Theme "Catppuccin Mocha"
Set TypingSpeed 50ms
Set Padding 20
Set Width 1400
Set Height 560

# Wait syncs to the prompt returning, so the demo advances when the
# command actually finishes instead of after a guessed Sleep.
Set WaitPattern /[$#>]\s*$/
Set WaitTimeout 90s

# The sandbox from docs/_static/demos/setup-sandbox.sh. Redirecting HOME,
# XDG_CONFIG_HOME, and TMUX_TMPDIR keeps real paths off screen and runs
# tmux on an isolated server: paths render as ~/... or /tmp/tmuxp-demo/...
Env HOME "/tmp/tmuxp-demo"
Env XDG_CONFIG_HOME "/tmp/tmuxp-demo/.config"
Env TMUX_TMPDIR "/tmp/tmuxp-demo/tmux"
Env PATH "/tmp/tmuxp-demo/bin:/usr/local/bin:/usr/bin:/bin"

Hide
Type "cd ~ && tmux kill-server 2>/dev/null; clear"
Enter
Show

Type "tmuxp import --help"
Enter
Wait
Sleep 2s
