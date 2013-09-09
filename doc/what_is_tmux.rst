.. _what_is_tmux:

What is tmux
============

Explain tmux like to me like I'm 5
----------------------------------

First, it is appropriate to place things in context.

In the world of computers, there are many dimensions:

1. The text dimension
2. The graphical dimension

Today, thanks to the power of things like fermi, the graphical dimension
of computers boot into games that transmute like 300 trillion polygons a
second.

This is about the text dimension. This is about fixed-width fonts and that
old fashioned black terminal.

tmux is to the consle what a graphical environment like your desktop in
os x, windows or linux, but inside the text dimension. Inside tmux you
can:

- multitask inside of a terminal, run multiple applications
- have multiple command lines in the same window
- have multiple windows in the workspace
- switch between workspaces, like virtual desktops

For users with some command line experience
-------------------------------------------

If you are a UNIX user, use command line and don't yet use a multiplexer,
like byoubu, screen or tmux, I'm excited to introduce you to tmux.

For GNU/screen user
-------------------

For users of GNU screen

For a current tmux user
-----------------------

tmuxp helps you save and load sessions.

For a current teamocil / tmuxinator / etc. user
-----------------------------------------------

- tmuxp requires python 2.7 on your system.
- the configuration format is slightly different.
- tmuxp allows configs in YAML, JSON, INI and :py:class:`dict` format.

For a pythonista
----------------

tmuxp is an abstraction of ``tmux(1)`` into python objects.

Uses ``sh`` for a clean :py:class:`subprocess` interface, ``kaplan`` for
configuration.

``unittest`` for tests. Tested in python 2.7.  You can read our :ref:`api`
documentation for more.

tmuxp is BSD licensed and it's VCS can be found at
http://github.com/tony/tmuxp.
