.. _examples:

========
Examples
========

2 split panes
-------------

YAML - Short form:

.. literalinclude:: ../examples/2-pane-vertical.yaml
    :language: yaml

YAML - Christmas Tree:

.. literalinclude:: ../examples/2-pane-vertical-long.yaml
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
