.. _about_tmux:

===============
The Tao of tmux
===============

.. figure:: _static/tao-tmux-screenshot.png
    :scale: 100%
    :width: 100%
    :align: center

    BSD-licensed terminal multiplexer.

tmux is geared for developers and admins who interact regularly with
CLI (text-only interfaces)

In the world of computers, there are 2 realms:

1. The text realm
2. The graphical realm

Tmux resides in the text realm. This is about fixed-width fonts and that
old fashioned black terminal.

tmux is to the console what a desktop is to gui apps. It's a world inside
the text dimension. Inside tmux you can:

- multitask inside the terminal, run multiple applications.
- have multiple command lines (pane) in the same window
- have multiple windows (window) in the workspace (session)
- switch between multiple workspaces, like virtual desktops

Thinking Tmux
=============

Text-based window manager
-------------------------

=================== ====================== ===============================
**tmux**            **"Desktop"-Speak**    **Plain English**
------------------- ---------------------- -------------------------------
Multiplexer         Multi-tasking          Multiple applications
                                           simulataneously.
Session             Desktop                Applications are visible here
Window              Virtual Desktop or     A desktop that stores it own
                                           applications
                    screen
Pane                Application            Performs operations
=================== ====================== ===============================

Multiple terminals in one screen
--------------------------------
Multiple applications or terminals to run on the same screen by splitting
up 1 terminal into multiple.

Being able to run 2 or more terminals on one screen is convenient. This
way one screen can be used to edit a file, and another may be used to
``$ tail -F`` a logfile.

.. aafig::

   +--------+--------+
   | $ bash | $ bash |
   |        |        |
   |        |        |
   |        |        |
   |        |        |
   |        |        |
   |        |        |
   +--------+--------+

.. aafig::

   +--------+--------+
   | $ bash | $ bash |
   |        |        |
   |        |        |
   +--------+--------+
   | $ vim  | $ bash |
   |        |        |
   |        |        |
   +--------+--------+

tmux supports as manys terminals as you want.

It allows multiple layouts to view the apps
-------------------------------------------

Different applications are viewable better in different layouts.

It allows switching between layouts such as...

Organize apps based on your needs
---------------------------------

You can categorize and keep many terminals / applications separated into
multiple windows.

In addition to being able to split the terminal into multiple panes, you
can create new windows as much as you want.

.. aafig::
   :textual:

   +---------+---------+                       
   | $ bash  | $ bash  |                       
   |         |         |                       
   |         |         |    /-----------------\
   +---------+---------+ -> |'switch-window 2'|
   | $ vim   | $ bash  |    \-----------------/
   |         |         |             |         
   |         |         |             |         
   +---------+---------+             |         
   | '1:sys*  2:vim'   |             |         
   +-------------------+             |         
                                    /
             /----------------------
             |
             v
   +---------+---------+
   | $ bash  | $ bash  |
   |         |         |
   |         |         |
   +---------+---------+
   | $ vim   | $ bash  |
   |         |         |
   |         |         |
   +---------+---------+
   | '1:sys*  2:vim'   |
   +-------------------+

You can switch between the windows you create.

Resume everything later
-----------------------

You can leave tmux and all applications running (detach), log out, make a
sandwich, and re-(attach), all applications are still running!

.. aafig::
   :textual:

   +--------+--------+                    
   | $ bash | $ bash |                    
   |        |        |                    
   |        |        |     /------------\ 
   +--------+--------+ --> |   detach   | 
   | $ vim  | $ bash |     | 'Ctrl-b b' |     
   |        |        |     \------------/     
   |        |        |            |           
   +--------+--------+            |           
               /------------------/
               |
               v
   +-----------------------+
   | $ [screen detached]   |
   |                       |
   |                       |
   |                       |
   |                       |
   |                       |
   |                       |
   +-----------------------+
               v
               |
               v
   +-----------------------+                   
   | $ [screen detached]   |                   
   | $ tmux attach         |                   
   |                       |     /------------\
   |                       | --> | attaching  |
   |                       |     \------------/
   |                       |           |
   |                       |           |
   +-----------------------+           |
                                      /
            /-------------------------
            |
            v
   +--------+--------+
   | $ bash | $ bash |
   |        |        |
   |        |        |
   +--------+--------+
   | $ vim  | $ bash |
   |        |        |
   |        |        |
   +--------+--------+

Manage workflow
---------------

- System administrators monitor logs and services.
- Programmers like to have an editor open with a CLI nearby.

Applications running on a remote server can be launched inside of a tmux
session, detached, and reattached next timeyour `"train of thought"`_ and
work.

Multitasking. Preserving the thinking you have. 

.. _"train of thought": http://en.wikipedia.org/wiki/Train_of_thought

Core Concepts
=============

.. seealso:: :ref:`glossary` has a dictionary of tmux words.

.. _server:

Server
------

A server contains :ref:`session`'s.

tmux starts the server automatically if it's not running.

In advanced cases, multiple can be run by specifying ``[-L socket-name]``
and ``[-S socket-path]``.

.. _client:

Client
------

Attaches to a tmux :ref:`server`.

.. _session:

Session
-------

Inside a tmux :ref:`server`.
    
The session has 1 or more :ref:`window`. The bottom bar in tmux show a
list of windows. Normally they can be navigated with ``Ctrl-a [0-9]``,
``Ctrl-a n`` and ``Ctrl-a p``.

Sessions can have a ``session_name``.

Uniquely identified by ``session_id``.

.. aafig::
    :textual:

    +----------------------------------------------------------------+
    |  +--------+--------+ +-----------------+ +-----------------+   |
    |  | pane   | pane   | | pane            | | pane            |   |
    |  |        |        | |                 | |                 |   |
    |  |        |        | |                 | |                 |   |
    |  +--------+--------+ |                 | +-----------------+   |
    |  | pane   | pane   | |                 | | pane            |   |
    |  |        |        | |                 | |                 |   |
    |  |        |        | |                 | |                 |   |
    |  +--------+--------+ +-----------------+ +-----------------+   |
    |  | window          | | window          | | window          |   |
    |  \--------+--------/ \-----------------/ \-----------------/   |
    +----------------------------------------------------------------+
    | session                                                        |
    \----------------------------------------------------------------/

.. _window:

Window
------

Entity of a :ref:`session`.

Can have 1 or more :ref:`pane`.

panes can be organized with a layouts.

windows can have names.

.. _pane:

Pane
----

Linked to a :ref:`window`.

a pseudoterminal.

.. _target:

Target
------

A target, cited in the manual as ``[-t target]`` can be a session, window
or pane.

License
-------

This page is licensed `Creative Commons BY-NC-ND 3.0 US`_.

.. _Creative Commons BY-NC-ND 3.0 US: http://creativecommons.org/licenses/by-nc-nd/3.0/us/
