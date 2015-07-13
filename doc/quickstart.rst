.. _quickstart:

==========
Quickstart
==========

Installation
------------

Assure you have at least tmux **>= 1.8** and python **>= 2.6**. For Ubuntu 12.04/12.10/13.04 users, you can download the tmux 1.8 package for Ubuntu 13.10 from `https://launchpad.net/ubuntu/+source/tmux <https://launchpad.net/ubuntu/+source/tmux>`_ and install it using dpkg.

.. code-block:: bash

    $ pip install tmuxp

You can upgrade to the latest release with:

.. code-block:: bash

    $ pip install tmuxp -U

Then install :ref:`bash_completion`.

Known issue on RHEL/CentOS/Fedora
---------------------------------

For all RedHat-based distros there might be an issue with starting tmuxp. 

    $ tmuxp
    Traceback (most recent call last):
      File "/usr/bin/tmuxp", line 5, in <module>
        from pkg_resources import load_entry_point
      File "/usr/lib/python2.6/site-packages/pkg_resources.py", line 2655, in <module>
        working_set.require(__requires__)
      File "/usr/lib/python2.6/site-packages/pkg_resources.py", line 648, in require
        needed = self.resolve(parse_requirements(requirements))
      File "/usr/lib/python2.6/site-packages/pkg_resources.py", line 546, in resolve
        raise DistributionNotFound(req)
    pkg_resources.DistributionNotFound: argparse

Try upgrading setuptools, has been proven to solve the problem on Fedora 22, CentOS 7 and RHEL 6. 

    sudo pip install -U setuptools

Can be tested in the Python REPL like this. 

    >>> import pkg_resources
    >>> pkg_resources.get_distribution('argparse')
    argparse 1.3.0 (/usr/lib/python2.6/site-packages)

The above operation would give the same exception (DistributionNotFound) before setuptools was upgraded. 


CLI
---

.. seealso:: :ref:`examples`, :ref:`cli`, :ref:`bash_completion`.

tmuxp launches workspaces / sessions from JSON and YAML files.

Configuration files can be stored in ``$HOME/.tmuxp`` or in project
directories as ``.tmuxp.py``, ``.tmuxp.json`` or ``.tmuxp.yaml``.

Every configuration is required to have:

1. ``session_name``
2. list of ``windows``
3. list of ``panes`` for every window in ``windows``

Create a file, ``~/.tmuxp/example.yaml``:

.. literalinclude:: ../examples/2-pane-vertical.yaml
    :language: yaml

.. code-block:: bash

    $ tmuxp load example.yaml

This creates your tmuxp session.


Pythonics
---------

.. seealso::
    :ref:`tmuxp python API documentation <api>` and :ref:`developing`,
    :ref:`internals`.


ORM - `Object Relational Mapper`_

AL - `Abstraction Layer`_

.. _Abstraction Layer: http://en.wikipedia.org/wiki/Abstraction_layer
.. _Object Relational Mapper: http://en.wikipedia.org/wiki/Object-relational_mapping

python abstraction layer
""""""""""""""""""""""""

.. module:: tmuxp

======================================== =================================
:ref:`tmuxp python api <api>`            :term:`tmux(1)` equivalent
======================================== =================================
:class:`Server.new_session()`            ``$ tmux new-session``
:class:`Server.list_sessions()`          ``$ tmux list-sessions``
:class:`Session.list_windows()`          ``$ tmux list-windows``
:class:`Session.new_window()`            ``$ tmux new-window``
:class:`Window.list_panes()`             ``$ tmux list-panes``
:class:`Window.split_window()`           ``$ tmux split-window``
:class:`Pane.send_keys()`                ``$ tmux send-keys``
======================================== =================================

tmux ORM
""""""""

tmuxp's core internal feature is the object relation and orchestration of
the tmux server (think an `engine`_ in `SQLAlchemy`_) and the server's
sessions, so on...

- :class:`Server` holds :class:`Session` objects.
- :class:`Session` holds :class:`Window` objects.
- :class:`Window` holds :class:`Pane` objects.

instances of tmux objects use tmux `1.8`_'s ``pane_id``, ``window_id`` and
``session_id`` to build create python objects to build workspaces with the
freshest data.

.. _engine: http://docs.sqlalchemy.org/en/rel_0_8/core/engines.html
.. _sqlalchemy: http://www.sqlalchemy.org/
.. _1.8: http://sourceforge.net/projects/tmux/files/tmux/tmux-1.8/
