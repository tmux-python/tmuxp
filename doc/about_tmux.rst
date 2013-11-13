.. _about_tmux:

===============
The Tao of tmux
===============

.. figure:: _static/tao-tmux-screenshot.png
    :scale: 60%
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
Sessio              Desktop                Applications are visible here
Window              Virtual Desktop or     A desktop that stores it own
                    applications           screen
Pane                Application            Performs operations
=================== ====================== ===============================

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

- 1 :term:`Server`.

  - has 1 or more :term:`Session`.

    - has 1 or more :term:`Window`.

      - has 1 or more :term:`Pane`.

.. seealso:: :ref:`glossary` has a dictionary of tmux words.

CLI Power Tool
--------------

Multiple applications or terminals to run on the same screen by splitting
up 1 terminal into multiple.

One screen can be used to edit a file, and another may be used to
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


.. aafig::
   :textual:

   +---------+---------+
   | $ bash  | $ bash  |
   |         |         |
   |         |         |     /-----------------\
   +---------+---------+ --> |'switch-window 2'|
   | $ vim   | $ bash  |     \-----------------/
   |         |         |              |
   |         |         |              |
   +---------+---------+              |
   | '1:sys*  2:vim'   |              |
   +-------------------+              |
             /------------------------/
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
   |                       |            |
   |                       |            |
   +-----------------------+            |
                                        |
            /---------------------------/
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

Installing tmux
===============

Tmux is packaged on most Linux and BSD systems.

For the freshest results on how to get tmux installed on your system,
"How to install tmux on <my distro>" will do, as directions change and are
slightly different between distributions.

This documentation is writtenf for version **1.8**. It's important that
you have the latest stable release of tmux. The latest stable version is
viewable on the `tmux homepage`_.

**Mac OS X** users may install that latest stable version of tmux through
`MacPorts`_, `fink`_ or `Homebrew`_ (aka brew).

If **compiling from source**, the dependencies are `libevent`_ and
`ncurses`_.

.. _tmux homepage: http://tmux.sourceforge.net/
.. _libevent: http://www.monkey.org/~provos/libevent/
.. _ncurses: http://invisible-island.net/ncurses/
.. _MacPorts: http://www.macports.org/
.. _Fink: http://fink.thetis.ig42.org/
.. _Homebrew: http://www.brew.sh

Using tmux
==========

Start a new session
-------------------

.. code-block:: bash

    $ tmux

That's all it takes to launch yourself into a tmux session.

.. tip:: Common pitfall

    Running ``$ tmux list-sessions`` or any other command for listing tmux
    entities (such as ``$ tmux list-windows`` or ``$ tmux list-panes``).
    This can generate the error "failed to connect to server".
    
    This could be because:

        - tmux server has killed its' last session, killing the server.
        - tmux server has encountered a crash. (tmux is highly stable,
          this will rarely happen)
        - tmux has not be launched yet at all.

.. _Prefix key:

The prefix key
--------------

Tmux hot keys have to be pressed in a special way. **Read this
carefully**, then try it yourself.

First, you press the *prefix* key. This is ``C-b`` by default.

Release. Then pause. For less than second. Then type what's next.

``C-b o`` means: Press ``Ctrl`` and ``b`` at the same time. Release,
Then press ``o``.

**Remember, prefix + short cut!** ``C`` is ``Ctrl`` key.

Session Name
------------

Sessions can be *named upon creation*.

.. code-block:: bash

    $ tmux new-session [-s session-name]

Sessions can be *renamed after creation*.

=============== =========================================================
Command         .. code-block:: bash

                    $ tmux rename-session <sesion-name>

Short cut       ``Prefix`` + ``$``
=============== =========================================================

Window Name
-----------

Windows can be *named upon creation*.

.. code-block:: bash

    $ tmuxp new-window [-n window-name]

.. _Rename window:

Windows can be *renamed after creation*.

=============== =========================================================
Command         .. code-block:: bash

                    $ tmux rename-window <new-name>

Short cut       ``Prefix`` + ``,``
=============== =========================================================

Creating new windows
--------------------

=============== =========================================================
Command         .. code-block:: bash

                    $ tmux new-window [-n window-name]

Short cut       ``Prefix`` + ``c``

                You may then :ref:`Rename window`.
=============== =========================================================

Traverse windows
----------------

By number

Next

.. code-block:: bash

    $ tmux next-window

Previous

.. code-block:: bash

    $ tmux previous-window

Last-window

.. code-block:: bash

    $ tmux last-window

===================   ====================================================
Short cut             Action
-------------------   ----------------------------------------------------
``n``                 Change to the next window.
``p``                 Change to the previous window.
``w``                 Choose the current window interactively.
``0 to 9``            Select windows 0 to 9.

``M-n``               Move to the next window with a bell or activity
                      marker.
``M-p``               Move to the previous window with a bell or activity
                      marker.

===================   ====================================================

Move windows
------------

Move window

.. code-block:: bash

    $ tmux move-window [-t dst-window]

Swap the window

.. code-block:: bash

    $ tmux swap-window [-t dst-window]

===================   ====================================================
Short cut             Action
-------------------   ----------------------------------------------------
``.``                 Prompt for an index to move the current window.
===================   ====================================================


Move panes
----------

.. code-block:: bash

    $ tmux move-pane [-t dst-pane]

===================   ====================================================
Short cut             Action
-------------------   ----------------------------------------------------
``C-o``               Rotate the panes in the current window forwards.
``{``                 Swap the current pane with the previous pane.
``}``                 Swap the current pane with the next pane.
===================   ====================================================


Traverse panes
--------------

Shortcut to move between panes.

.. code-block:: bash

    $ tmux last-window


===================   ====================================================
Short cut             Action
-------------------   ----------------------------------------------------
``Up, Down``          Change to the pane above, below, to the left, or to
``Left, Right``       the right of the current pane.
===================   ====================================================


Recipe (todo): tmux conf to ``hjkl`` commands

Kill window
-----------

.. code-block:: bash

    $ tmux kill-window

===================   ====================================================
Short cut             Action
-------------------   ----------------------------------------------------
``&``                 Kill the current window.
===================   ====================================================


Kill pane
---------

===================   ====================================================
Short cut             Action
-------------------   ----------------------------------------------------
``x``                 Kill the current pane.
===================   ====================================================

Kill window
-----------

===================   ====================================================
Short cut             Action
-------------------   ----------------------------------------------------
``&``                 Kill the current window.
===================   ====================================================

Splitting windows into panes
----------------------------

Tmux windows can be split into multiple panes.

===================   ====================================================
Short cut             Action
-------------------   ----------------------------------------------------
``%``                 Split the current pane into two, left and right.
``"``                 Split the current pane into two, top and bottom.
===================   ====================================================




Tmux configuration
==================

Tmux can be configured via a configuration at ``~/.tmux.conf``.

Depending on your tmux version, there is different options available.

- Status lines
- Short cuts


Reference
=========

Short cuts
----------

.. tip::

    :ref:`Prefix key` is pressed before a short cut!

===================   ====================================================
Short cut             Action
-------------------   ----------------------------------------------------
``C-b``               Send the prefix key (C-b) through to the
                      application.
``C-o``               Rotate the panes in the current window forwards.
``C-z``               Suspend the tmux client.
``!``                 Break the current pane out of the window.
``"``                 Split the current pane into two, top and bottom.
``#``                 List all paste buffers.
``$``                 Rename the current session.
``%``                 Split the current pane into two, left and right.
``&``                 Kill the current window.
``'``                 Prompt for a window index to select.
``,``                 Rename the current window.
``-``                 Delete the most recently copied buffer of text.
``.``                 Prompt for an index to move the current window.
``0 to 9``            Select windows 0 to 9.
``:``                 Enter the tmux command prompt.
``;``                 Move to the previously active pane.
``=``                 Choose which buffer to paste interactively from a
                      list.
``?``                 List all key bindings.
``D``                 Choose a client to detach.
``[``                 Enter copy mode to copy text or view the history.
``]``                 Paste the most recently copied buffer of text.
``c``                 Create a new window.
``d``                 Detach the current client.
``f``                 Prompt to search for text in open windows.
``i``                 Display some information about the current window.
``l``                 Move to the previously selected window.
``n``                 Change to the next window.
``o``                 Select the next pane in the current window.
``p``                 Change to the previous window.
``q``                 Briefly display pane indexes.
``r``                 Force redraw of the attached client.
``s``                 Select a new session for the attached client
                      interactively.
``L``                 Switch the attached client back to the last session.
``t``                 Show the time.
``w``                 Choose the current window interactively.
``x``                 Kill the current pane.
``{``                 Swap the current pane with the previous pane.
``}``                 Swap the current pane with the next pane.
``~``                 Show previous messages from tmux, if any.
``Page Up``           Enter copy mode and scroll one page up.
``Up, Down``          Change to the pane above, below, to the left, or to
``Left, Right``       the right of the current pane.
``M-1 to M-5``        Arrange panes in one of the five preset layouts:
                      even-horizontal, even-vertical, main-horizontal,
                      main-vertical, or tiled.
``M-n``               Move to the next window with a bell or activity
                      marker.
``M-o``               Rotate the panes in the current window backwards.
``M-p``               Move to the previous window with a bell or activity
                      marker.
``C-Up, C-Down``      Resize the current pane in steps of one cell. 
``C-Left, C-Right``
``M-Up, M-Down``      Resize the current pane in steps of five cells.
``M-Left, M-Right``
===================   ====================================================

Source: tmux manpage [1]_.

.. [1] See the ``tmux.1`` at
   http://sourceforge.net/p/tmux/tmux-code/ci/master/tree/tmux.1 and use
   
   .. code-block:: bash
   
       $ nroff -mdoc tmux.1|less

License
-------

This page is licensed `Creative Commons BY-NC-ND 3.0 US`_.

.. _Creative Commons BY-NC-ND 3.0 US: http://creativecommons.org/licenses/by-nc-nd/3.0/us/
