.. module:: tmuxp

.. _about:

=====
About
=====

tmuxp helps you manage tmux workspaces.

Built on a object relational mapper for tmux. tmux users can reload common
workspaces from YAML, JSON and :py:obj:`dict` configurations like
`tmuxinator`_ and `teamocil`_.

To jump right in, see :ref:`quickstart` and :ref:`examples`.

Interested in some kung-fu or joining the effort? :ref:`api` and
:ref:`developing`.

`BSD-licensed`_. Code on `github 
<http://github.com/tony/tmuxp>`_.

Differences from tmuxinator / teamocil
--------------------------------------

.. note::

    If you use teamocil / tmuxinator and can clarify or add differences,
    please free to `edit this page`_ on github.

Similarities
~~~~~~~~~~~~

**Load sessions** Loads tmux sessions from config

**YAML** Supports YAML format

**Inlining / shorthand configuration** All three support short-hand and
simplified markup for panes that have one command.

**Maturity and stability** As of 2016, all three are considered stable,
well tested and adopted.

Missing
~~~~~~~

**Version support** tmuxp only supports ``tmux >= 1.8``. Teamocil and
tmuxinator may have support for earlier versions.

Differences
~~~~~~~~~~~

**Programming Language** python. teamocil and tmuxinator uses ruby.

**Workspace building process** teamocil and tmuxinator process configs
directly shell commands. tmuxp processes configuration via ORM layer.

Additional Features
-------------------

**CLI** tmuxp's CLI can attach and kill sessions with tab-completion
support. See :ref:`commands`.

**Import config** import configs from Teamocil / Tmuxinator [1]_. See
:ref:`cli_import`.

**Session freezing** Supports session freezing into YAML and JSON
format [1]_. See :ref:`cli_freeze`.

**JSON config** JSON config support. See :ref:`Examples`.

**ORM-based API** - Utilitizes tmux >= 1.8's unique ID's for panes,
windows and sessions to create an object relational view of the tmux
:class:`Server` and its' :class:`Session`, :class:`Window`, :class:`Pane`.
See :ref:`Internals`.

**Conversion** ``$ tmuxp convert <filename>`` can convert files to and
from JSON and YAML.

.. [1] While freezing and importing sessions is a great way to save time, 
       tweaking will probably be required - There is no substitute to a
       config made with love.

Minor tweaks
------------

- Unit tests against live tmux version to test statefulness of tmux
  sessions, windows and panes. See :ref:`travis`.
- Load + switch to new session from inside tmux.
- Resume session if config loaded.
- Pre-commands virtualenv / rvm / any other commands.
- Load config from anywhere ``$ tmuxp load /full/file/path.json``.
- Load config ``.tmuxp.yaml`` or ``.tmuxp.json`` from current working
  directory with ``$ tmuxp load .``.
- ``$ tmuxp -2``, ``$ tmuxp -8`` for forcing term colors a la
  :term:`tmux(1)`.
- ``$ tmuxp -L<socket-name>``, ``$ tmuxp -S<socket-path>`` for sockets and
  ``$ tmuxp -f<config-file>`` for config file.

More details
------------

.. include:: ../README.rst
    :start-after: ---------------

.. _attempt at 1.7 test: https://travis-ci.org/tony/tmuxp/jobs/12348263
.. _kaptan: https://github.com/emre/kaptan
.. _BSD-licensed: http://opensource.org/licenses/BSD-2-Clause
.. _tmuxinator: https://github.com/aziz/tmuxinator
.. _teamocil: https://github.com/remiprev/teamocil
.. _ERB: http://ruby-doc.org/stdlib-2.0.0/libdoc/erb/rdoc/ERB.html
.. _edit this page: https://github.com/tony/tmuxp/edit/master/doc/about.rst
