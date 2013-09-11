`tmuxp` solves the panes / pains of managing workspaces

tmuxp was written from the ground up as an ORM layer on top of tmux.

under development, not ready for public use.

Current issues
--------------


Slated for 0.2
--------------

- (#1) travis compatible unittests (this requires attention to client.
  workaround: have a tmux client open in another terminal to run unit
  tests.
- (#2) support for support multiple Tmux servers and custom config
  ``Server`` object:
  - tmux config ``file``, aka ``[-f file]``
  - tmux server ``socket_name``, aka ``[-L socket-name]``
  - tmux server ``socket_path``, aka ``[-S socket-path]``

Goals
-----

- high-level python abstraction of tmux to automate session, window and
  pane management
- support multiple configuration formats (json, yaml)
- freeze current tmux session, window, and panes into rough configs,
  perhaps to ~/.tmuxp/snapshots/(year-month-day-(optname))/session.yaml
- bash / zsh autocomplete
- resume to normal workflow, or last snapshot of sessions
- strives for purity to tmux and python

what's done
-----------

- config reading from/to JSON, yaml with kaplan
- foundation for unit tests
- basic creation of sessions, windows, panes
- pythonic abstraction / ORM of all tmux sessions, windows, panes
- ``Server`` can create ``.new_session``, ``.list_sessions``
- more...

How tmuxp works
---------------

Note that ``tmux(1)`` is the real app, hereinafter 'tmux'. ``tmuxp``
is this script.

tmux returns data with its commands. tmux allows a custom response with
the use of ``formatters``. tmuxp uses these commands to keep a fresh
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
