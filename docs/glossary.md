(glossary)=

# Glossary

```{glossary}

tmuxp
    A tool to manage workspaces with tmux. A pythonic abstraction of
    tmux.

tmux
tmux(1)
    The tmux binary. Used internally to distinguish tmuxp is only a
    layer on top of tmux.

ConfigReader
    configuration management class, for parsing YAML / JSON / etc. files
    to and from python data (dictionaries, in the future, potentially
    dataclasses)

Server
    tmux runs in the background of your system as a process.

    A server holds one or more {term}`Session`. tmux starts the server
    automatically the first time ``$ tmux`` runs, if it isn't already
    running.

    Advanced: you can run more than one by specifying
    ``[-L socket-name]`` or ``[-S socket-path]``.

Client
    Attaches to a tmux {term}`server`.  When you use tmux through CLI,
    you are using tmux as a client.

Session
    Inside a tmux {term}`server`.

    The session has 1 or more {term}`Window`. The bottom bar in tmux
    show a list of windows. Normally they can be navigated with
    ``Ctrl-a [0-9]``, ``Ctrl-a n`` and ``Ctrl-a p``.

    Sessions can have a ``session_name``.

    Uniquely identified by ``session_id``.

Window
    Entity of a {term}`session`.

    Can have 1 or more {term}`pane`.

    Panes can be organized with layouts.

    Windows can have names.

Pane
    Linked to a {term}`Window`.

    a pseudoterminal.

Target
    A target, cited in the manual as ``[-t target]`` can be a session,
    window or pane.
```
