.. _about_tmux:


About tmux
==========

Tmux is a terminal multiplexer.

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

1. It allows multiple applications or terminals to run at once.

Being able to run 2 or more terminals on one screen is convenient. This
way one screen can be used to edit a file, and another may be used to
``$ tail -F`` a logfile.

You can create and remove as many terminal as you want.

2. It allows multiple layouts to view the apps.

Different applications are viewable better in different layouts.

It allows switching between layouts such as...

3. You can categorize and keep many terminals / applications separated
   into multiple windows.

So actually, in addition to being able to split the terminal into multiple
windows, you can create new spaces as much as you want.

You can leave the window, and return later, and your applications will
still be there.

4. You can leave tmux and all applications inside (detach), log out, make
   a sandwich, and re-(attach), all applications are still running!

So you can keep tmux on a server with your latest work, come back and
resume your `"train of thought"`_ and work.


More than anything - the take-away from tmux is multitasking. More than
any technical jargon - it's preserving the thought you have, whether you
were in the midst of a one-off task, or a common task.

If you do a task commonly, it may help to use an application which manages
tmux workspaces.

.. _"train of thought": http://en.wikipedia.org/wiki/Train_of_thought
