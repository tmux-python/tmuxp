.. _quickstart:

==========
Quickstart
==========

Tmux Session Manager
--------------------

tmuxp launches sessions from a configuration file.

Configuration files can be stored in ``$HOME/.tmuxp`` or in project
directories as ``.tmuxp.py``, ``.tmuxp.json`` or ``.tmuxp.yaml``.

Every configuratio is required to have:

1. ``session_name``
2. list of ``windows``
3. list of ``panes`` for every window in ``windows``

Create a file, ``~/.tmuxp/example.yaml``:

.. literalinclude:: ../examples/2-pane-vertical.yaml
    :language: yaml

with tmuxp:

.. code-block:: bash

    $ tmuxp -l

It will list configs available in the current directory and
``$HOME/.tmuxp``. ``example.yaml`` is detected by tmuxp. 

.. code-block:: bash

    $ tmuxp example.yaml

This creates your tmuxp session.

.. seealso:: :ref:`examples`

Bash completion
"""""""""""""""

.. note::

    Parts of the zsh, bash and tcsh completion and these docs are based on
    `aws cli`_.

For bash:

.. code-block:: bash

    $ complete -C tmuxp.bash tmuxp

For tcsh:

.. code-block:: bash

    $ complete tmuxp 'p/*/`tmuxp.bash`/'

For zsh:

.. code-block:: bash

    $ source tmuxp.zsh

.. _aws cli: https://github.com/aws/aws-cli

Python ORM + AL
---------------

ORM - Object Relational Mapper

AL - Abstraction Layer

Conventions
"""""""""""

.. module:: tmuxp

.. seealso::
    :ref:`tmuxp python API documentation <api>` and :ref:`developing`.

======================================== =================================
:ref:`tmuxp python api <api>`            :term:`tmux(1)` equivalent
======================================== =================================
:class:`Server.list_sessions()`          ``$ tmux list-sessions``
:class:`Session.list_windows()`          ``$ tmux list-windows``
:class:`Window.list_panes()`             ``$ tmux list-panes``
:class:`Server.new_session()`            ``$ tmux new-session``
:class:`Session.new_window()`            ``$ tmux new-window``
:class:`Window.split_window()`           ``$ tmux split-window``
:class:`Pane.send_keys()`                ``$ tmux send-keys``
======================================== =================================

tmux ORM
""""""""

tmuxp's main internal feature is to abstract tmux into relational objects.

- :class:`Server` holds :class:`Session` objects.
- :class:`Session` holds :class:`Window` objects.
- :class:`Window` holds :class:`Pane` objects.
