.. _examples:

========
Examples
========

2 split panes
-------------

.. sidebar:: 2 pane

    .. aafig::

        +-----------------+
        | $ pwd           |
        |                 |
        |                 |
        +-----------------+
        | $ pwd           |
        |                 |
        |                 |
        +-----------------+

YAML - Short form:

.. literalinclude:: ../examples/2-pane-vertical.yaml
    :language: yaml

YAML - Christmas Tree:

.. literalinclude:: ../examples/2-pane-vertical-long.yaml
    :language: yaml

3 panes
-------

.. sidebar:: 3 panes

    .. aafig::

        +-----------------+
        | $ pwd           |
        |                 |
        |                 |
        +--------+--------+
        | $ pwd  | $ pwd  |
        |        |        |
        |        |        |
        +--------+--------+

.. literalinclude:: ../examples/3-pane.yaml
    :language: yaml

4 panes
-------

.. sidebar:: 4 panes

    .. aafig::

        +--------+--------+
        | $ pwd  | $ pwd  |
        |        |        |
        |        |        |
        +--------+--------+
        | $ pwd  | $ pwd  |
        |        |        |
        |        |        |
        +--------+--------+

.. literalinclude:: ../examples/4-pane.yaml
    :language: yaml

Super-advanced dev environment
------------------------------

.. seealso::
    :ref:`tmuxp developer config` in the :ref:`developing` section.

.. literalinclude:: ../.tmuxp.yaml
    :language: yaml

Kung fu
-------

.. note::

    tmuxp sessions can be scripted in python. The first way is to use the
    ORM in the :ref:`API`. The second is to pass a :py:obj:`dict` into
    :class:`tmuxp.WorkspaceBuilder` with a correct schema. See:
    :meth:`tmuxp.config.check_consistency`.

Add yours? Submit a pull request to the `github`_ site!

.. _github: https://github.com/tony/tmuxp
