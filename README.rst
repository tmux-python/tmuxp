`tmuxwrapper` was invented to solve the panes / pains of managing
workspaces

under development, not ready for public use

Goals
-----

- high-level python abstraction of tmux to automate session, window and
  pane management
- support multiple configuration formats (json, yaml)
- freeze current tmux session, window, and panes into rough configs, perhaps
  to ~/.tmuxwrapper/snapshots/(year-month-day-(optionalname))/session.yaml
- bash / zsh autocomplete
- resume to normal workflow, or last snapshot of sessions


hierarchy
---------

::

   session(s)
       - cmds (str like 'htop' or list ['pwd', 'htop'])
       - root (str dir path, like '/var/www')
       - window(s)
           - cmd(s)
           - root
           - panes(s)
               - dimensions
               - cmd(s)
               - root

cmd, cwd can be added at the session, window and pane level.

the deepest will have precedence. a command or cwd at the session level
will apply to all windows, panes within it. a command or cwd at window
level applies to all panes. a pane may specify its own cmd.

advanced sorcery
----------------

before_cmd / after_cmd
""""""""""""""""""""""

tbd, but commands will be able to be go before/after commands on any
level also. for instance, session may run before_cmd: and all windows
and panes within will run accordingly

aliases
"""""""

a common command may be aliased as a shortcut to prevent duplication.
syntax for this is still subject to change

under the hood
--------------

the internals of tmux is a tool kit, a high level abstraction of Sessions,
Windows and Panes.

the code is very simple. kaplan will read any type of config file and
turn it into a python dictionary. for brevity, tmuxwrapper offers a
few inline expressions, such as (in YAML):

``mywindow: my_cmd``

which is expanded to:

::

    {
        name: 'mywindow',
        panes: [
            cmds: ['my_cmd']
        ]
    }

Session, Window, Pane are all python classes which accept options and
print out as a __dict__ and __cmd__.

- ``__dict__``: ``dict`` : a fully expanded python dictionary configuration for  the object.
- ``to_json()``: ``str`` : export the object to JSON config format
- ``to_yaml()``: ``str`` : export the object to YAML config
- ``to_ini()``: ``str`` : export object to INI config

How a session is built:

* A ``Session`` object holds ``Window``(s)
* A ``Window`` holds ``Panes``

They are meant to provide a clear abstraction of tmux's api.

How do the panes / windows accept configuration from windows and
sessions?

A Session() object may be created by itself, but the __init__ will
check for a Window object and Session object. This assures that Windows
and Panes can inherit the cmd's, root dirs and before_cmd and
after_cmd.

Roadmap
-------

- To a degree, be able to pull running tmux sessions, windows and panes
  into Session, Window, and Pane objects and therefore be exportable
  into configs. A la, many attempts before, a ``pip freeze``.
- The biggest difficulty is keeping the abstraction of tmux pure and
  pythonic.
- A workflow to test a configuration file, launch tmux session/windows/panes
  with a ctrl-a ``tbd`` to ``kill-session`` and monitor config file for changes,
  lint it, create a new session, switch to it, and ``kill-session`` the old
  one.
- Check for ``.hg`` and ``.git`` in ``$HOME/.tmuxwrapper``, set a
  notification if it is out of date.
- Have ``freeze`` check for ``virtualenv``, ``rvm``, ``perlbrew`` and add
  it to the ``before_cmd``.
- grab pane when new_session created
- session.new_window
- create session.[windowindex] = Window or session.w.[window index] = Window ?
- session.to_yaml() export config to yaml
- session.to_yaml().save('filename')
- session.from_yaml().load('filename')
- cli: allow loading session   tmw filename.{yaml, json, ..} to load,
  - catch has-session, prompt to rename
  - possibility: open to ``-t`` group session to target?
- cli: and definitely bashcomplete json/yaml/ini files + commands
- cli: replicate tmux commands too
- window.split_pane to split-pane
- experiment: have windows with 1 pane have access to pane objects?
- have session inherit  window methods of the current active window
  such as session.next_layout is now available
- have window inherit some pane methods of current pane? only if just 1?
- experiment: using .send-keys can be done on session, window and pane
  level for power?
- experiment: Server object for managing / orchestrating across sessions?
- pane.send_keys for send-keys

Reference
---------

* tmux docs http://www.openbsd.org/cgi-bin/man.cgi?query=tmux&sektion=1
