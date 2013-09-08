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

testing
-------

See documentation in [./tmux/testsuite/__init__.py](https://github.com/tony/tmuxwrapper/blob/master/tmux/testsuite/__init__.py).

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


How tmuxwrapper works
---------------------

Note that ``tmux(1)`` is the real app, hereinafter 'tmux'. ``tmuxwrapper``
is this script.

tmux returns data with its commands. tmux allows a custom response with
the use of ``formatters``. tmuxwrapper uses these commands to keep a fresh
list of act sessions, windows and panes.

If you want to play with the internals of tmux, I highly recommend
wrapping your brain around (Not reading, but understanding) the manpage
for tmux.

Session, Window and Pane informations are all stored in python object's
which hold the raw data returned from tmux. The objects are a subclass of
``TmuxObject``, which is a ``collections.MutableMapping``. More simply,
the object stores dict data in the background as ``._TMUX`` but you just
need to do (say ``p`` is an instance of ``Pane``) ``p.get('session_id')``
and you will get the session_id. This is similar to the way a Backbone
model uses ``attributes`` object literal holds model data.

advanced sorcery
----------------

before_cmd / after_cmd
""""""""""""""""""""""

tbd, but commands will be able to be go before/after commands on any
level also. for instance, session may run before_cmd: and all windows
and panes within will run accordingly

under the hood
--------------

This is subject to change.

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
- tmux session config generator
  - log god: scan /var/log /opt/etc/var/log/ for apache2, nginx, Xorg and
    create a session with windows reading logs of common 90% cases.
  - web warrior: check for apache2/nginx/php/supervisor/upstart etc dirs
    and make a session for that.
  - dot config: check for .vim .config/awesome .tmux.conf and make a
    session with windows for those config files
- feature like `z` to attach search session name / windows name / pane
  directory, pane apps, and finally buffers to attach directly to that
  session.  note `find-window` does this.
- docs in this style?
  http://docs.python-guide.org/en/latest/notes/styleguide/
- should ._TMUX metadata make passing Session and Window objects into new
  Window and Pane objects obsolete? look at thread locals / global
- contextmanager's and with to iterate over a server, session, window
- contextmanager iterate for all panes that have an attribute (directory,
  window_name, etc)
- global for server, contains sessions, attribute _session and
  _window object references global / thread local
- ipython notebook try using fbcat + imagemagick convert to see results
  of tmux changes.  fbgrab + tty works well for demonstration
- also look into scrot, x11 solutions and
  https://github.com/KittyKatt/screenFetch
- control mode, for longer tmuxwrapper sessions where references to
  objects are needed to be updated and shown they've gone stale (a pane
  object that has been closed needs to be changed to being stale, a window
  object that has been renamed needs to have its window_name updated)
- and one more thing
- vim: may be used inside of a pane object with a filename (relative to
  the pane dir, also accepts /) and vim windows may be split and opened
- support for importing teamocil and tmuxinator configs
- creating a pane / window should return the new object, then refresh the
  parent (list_sessions for server, list_windows for session, list_panes
  for window).
- renaming or moving a pane should always return the object session,
  window or pane object and flush/refresh the contents of the tmux server
  objects (sessions, windows, panes).
- if an object is removed from the list, any reference to it should be
  changed. since python doesn't use pointers/references like other
  languages, a pubsub like blinker http://pythonhosted.org/blinker/ or ee
  https://github.com/jesusabdullah/pyee.
- remove ._TMUX, use collections.MutableMapping. check for {session,
  window,pane}_id to see if its a live tmux object. use kwargs.pop() for
  session, window, pane.
- create and test a compact / inline config format.
- a C-type of binding to pull server/session/window/pane information
  directly from tmux.
- support for show-options and setting options via ``.options`` on session
  and window.
- automatically handle rename-window when the value of the window-name is
  set. this gives an abstraction of tmux that is then 'model-driven' like
  backbone js, but also a pythonic abstraction.
- unit test roadmap.
  - test schema, types of objects
  - parsing of config types. export of config types
  - config expand
  - config inliner script
  - config passthru / hierarchy
  - export a current tmux session to tmux objects, then config
  - data driven tmux, handle options, renames
  - swapping windows using objects, swapping panes using Pane objects,
    linking or moving windows via Session.
- remember that new-window without ``shell-command`` with run option
  ``default-command`` if used.

Roadmap
-------

0.1
"""

- verbose config structure
- yaml support
- docs
  - for install from github
  - code docs
  - ipython notebook overview of internals
  - example config files
  - before_cmd, after_cmd

-dev
""""

- python package
- python version compatability (tested in 2.7 now)
- tmux version compatibility (using git version now)
- unit testing
- packages for ubuntu, debian, redhat, fedora, arch, BSD's, etc.
- video overview

Similarities to Tmux and Pythonics
----------------------------------

tmuxwrapper is was built in the spirit of understanding how tmux operates
and how python objects and tools can abstract the API's in a pleasant way.

tmuxwrapper uses the identify ``FORMATTERS`` used by tmux, you can see
them inside of http://sourceforge.net/p/tmux/tmux-code/ci/master/tree/format.c.

In this, I will also begin documenting the API.

the use of:

Session
Session.new_window() - returns a new Window object bound to the session,
also uses ``tmux new-window``.
Session.new_session() - class method - returns a new Session object.

Differences from tmux
---------------------

Because this is a python abstraction and flags like ``start-directory``
have dashes (-) replaced with underscores (_).

interesting observations
------------------------

How is tmuxwrapper able to keep references to panes, windows and sessions?

    Tmux has unique ID's for sessions, windows and panes.

    panes use ``%``, such as ``%1234``

    windows use ``@``, such as ``@2345``

    sessions use ``$``, for money, such as ``$``



How is tmuxwrapper able to handle windows with no names?

    Tmux provides ``window_id`` as a unique identifier.

What is a {pane,window}_index vs a {pane,window,session}_id?

    Pane index refers to the order of a pane on the screen.

    Window index refers to the # of the pane in the session.

Reference
---------

* tmux docs http://www.openbsd.org/cgi-bin/man.cgi?query=tmux&sektion=1
* tmux source code http://sourceforge.net/p/tmux/tmux-code/ci/master/tree/
