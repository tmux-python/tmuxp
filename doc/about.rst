.. module:: tmuxp

.. _about:

=====
About
=====

tmuxp helps you manage your text-based workspaces. Its BSD licensed.

Internally, tmuxp is an object relational mapper on top of tmux.
End-users may use YAML, JSON and :py:obj:`dict` configurations to launch
workspaces like `tmuxinator`_ and `teamocil`_.

To jump right in, see :ref:`quickstart` and :ref:`examples`.

Interested in some kung-fu or joining the effort? :ref:`api` and
:ref:`developing`

License  is `BSD-licensed`_. Code can be found at github at
http://github.com/tony/tmuxp.

Differences from tmuxinator / teamocil
--------------------------------------

.. note::

    If you use teamocli / tmuxinator and can clarify or add differences,
    please free to `edit this page`_ on github.

Similarities
""""""""""""

**Load sessions** Loads tmux sessions from config

**YAML** Supports YAML format

**Inlining / shorthand configuration** All three support short-hand and
simplified markup for panes that have one command.

Missing
"""""""

**Stability** tmuxinator and teamocil are far more stable and
well-developed than tmuxp.

**ERB / Template support** teamocil supports `ERB`_ markup.

**Version support** tmuxp only supports ``tmux >= 1.8``. Teamocil and
tmuxinator may have support for earlier versions.

Differences
"""""""""""

**Programming Language** python. teamocil and tmuxinator uses ruby.

**Internals** teamocil and tmuxinator pipe configurations into
commands. tmuxp turns configuration into a live :class:`Session` object
with access to all window and pane data. See :ref:`ORM_AL`.

**CLI** tmuxp's CLI can attach and kill sessions.

Additional Features
"""""""""""""""""""

**Unit tests** Tests against live tmux version to test statefulness of
tmux sessions, windows and panes. See :ref:`travis`.

**Import config** import configs from Teamocil / Tmuxinator *****

**Session freezing** Supports session freezing into YAML and JSON
format *****.

**JSON config** JSON config support

**Conversion** ``$ tmuxp convert <filename>`` can convert files to and
from JSON and YAML.

Footnotes
"""""""""

* Tmuxp session configurations can be very complicated, importing and
  freezing sessions may save a lot of time, but tweaking will probably be
  required. There is no substitute for a config made with love.

.. _attempt at 1.7 test: https://travis-ci.org/tony/tmuxp/jobs/12348263
.. _kaptan: https://github.com/emre/kaptan
.. _unittest: http://docs.python.org/2/library/unittest.html
.. _BSD-licensed: http://opensource.org/licenses/BSD-2-Clause
.. _tmuxinator: https://github.com/aziz/tmuxinator
.. _teamocil: https://github.com/remiprev/teamocil
.. _ERB: http://ruby-doc.org/stdlib-2.0.0/libdoc/erb/rdoc/ERB.html
.. _edit this page: https://github.com/tony/tmuxp/edit/master/doc/about.rst
