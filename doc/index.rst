.. sidebar:: $ tmuxp

    .. aafig::

        +--------+--------+
        |        |        |
        |        |        |
        |        |        |
        +--------+--------+
        |        |        |
        |        |        |
        |        |        |
        +--------+--------+

tmuxp
=====

tmuxp, a novel approach to managing :term:`tmux(1)` workspaces through
python objects, with configuration loading in JSON, YAML and
:py:obj:`dict` included.

tmuxp works in 3 ways:

- a pythonic `abstraction layer`_ on top of tmux' CLI commands
- an `ORM`_ that internally orchestrates relations between servers,
  sessions, windows and panes for good and evil purposes.
- CLI tmux session manager, similar to `teamocil`_ and `tmuxinator`, with
  support for YAML, JSON and python dicts.

More soon? You betcha`

.. _abstraction layer: http://en.wikipedia.org/wiki/Abstraction_layer
.. _ORM: http://en.wikipedia.org/wiki/Object-relational_mapping

Explore:

.. toctree::
    :maxdepth: 2

    about
    about_tmux
    quickstart
    examples
    developing
    api
    glossary
    changes



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

