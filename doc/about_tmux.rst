.. _about_tmux:

===============
The Tao of tmux
===============

BSD-licensed terminal multiplexer.

=================== ====================== ===============================
tmux Speak              Desktop Speak           English
------------------- ---------------------- -------------------------------
Multiplexer         Multitasking           Do more than one thing at the
                                           same time.
Session             Desktop                Where stuff gets done
Window              Virtual Desktop or     Where my windows are at
                    screen
Pane                Application            Does things
=================== ====================== ===============================


The usability benefits of tmux build upon themselves below:

Multiple terminals to one screen
--------------------------------
It allows multiple applications or terminals to run at once.

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

You can create and remove as many terminal as you want.

It allows multiple layouts to view the apps
-------------------------------------------

Different applications are viewable better in different layouts.

It allows switching between layouts such as...

Organize apps based on your needs
---------------------------------
You can categorize and keep many terminals / applications separated into
multiple windows

In addition to being able to split the terminal into multiple windows, you
can create new spaces as much as you want.

You can leave the window, and return later, and your applications will
still be there.

Resume everything later
-----------------------

You can leave tmux and all applications running (detach), log out, make a
sandwich, and re-(attach), all applications are still running!

.. aafig::

   +--------+--------+                        +-----------------------+
   | $ bash | $ bash |                        | '$ [screen detached]' |
   |        |        |                        |                       |
   |        |        |     /------------\     |                       |
   +--------+--------+ --> | 'detach'   | --> |                       |
   | $ vim  | $ bash |     | 'ctrl-b b' |     |                       |
   |        |        |     \------------/     |                       |
   |        |        |                        |                       |
   +--------+--------+                        +-----------------------+
                                                           |
            +----------------------------------------------+
            |
            v
   +-----------------------+                        +--------+--------+
   | '$ [screen detached]' |                        | $ bash | $ bash |
   | '$ tmux attach'       |                        |        |        |
   |                       |     /------------\     |        |        |
   |                       | --> | 'attaching'| --> +--------+--------|                       |
   |                       |     \------------/     | $ vim  | $ bash |
   |                       |                        |        |        |
   |                       |                        |        |        |
   +-----------------------+                        +-----------------+

The take-away
-------------
So you can keep tmux on a server with your latest work, come back and
resume your `"train of thought"`_ and work.

More than anything - the take-away from tmux is multitasking. More than
any technical jargon - it's preserving the thought you have, whether you
were in the midst of a one-off task, or a common task.

If you do a task commonly, it may help to use an application which manages
tmux workspaces.

.. _"train of thought": http://en.wikipedia.org/wiki/Train_of_thought


Getting more technical
======================

tmux is not the only multiplexer. there is also screen.

tmux is comprised of these objects:

server
------
multiple can be run by specific ``[-L socket-name]`` and ``[-S socket-path]``.

holds sessions.
    
session
-------

inside a server.
    
holds windows.

windows can have a name.

======= ==================================================
options most to least important options la

formats most to least important options hi
======= ==================================================

window
------
inside a session.

holds panes.

panes can be organized with a layouts.

windows can have names.

======= ==================================================
options most to least important options la

formats most to least important options hi
======= ==================================================

pane
----
inside / Linked to a window.

a pty (pseudoterminal).

======= ==================================================
options most to least important options la

formats most to least important options hi
======= ==================================================

which are described by:
options - settings for the pane, window, session or server
formats - variables describing the current "state" of the object
