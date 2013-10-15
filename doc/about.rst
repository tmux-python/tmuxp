.. _about:

===========
About tmuxp
===========

tmux users
----------

tmuxp helps you manage your text-based workspaces. Its BSD licensed,
modelled after tmux's ``commands`` and ``formats``.

.. note::

    Currently tmuxp is tested with 1.8 and above. It is recommended to
    update to the latest version. If there is enough demand, support can
    be added to support older versions.

    1.7 and below issues:

    tmuxp relies on the ``-P`` option to print out session information
    when ``new-session`` is called (see `attempt at 1.7 test`_).

teamocil / tmuxinator / etc.
----------------------------

- tmuxp requires python 2.7 on your system.
- the configuration format is slightly different.
- tmuxp allows configs in YAML, JSON, and :py:class:`dict` format.

developer info
--------------

.. seealso::
    :ref:`api`
    :ref:`developing`

License
"""""""

tmuxp is `BSD-licensed`_.

Source
""""""

Code can be found at github at http://github.com/tony/tmuxp.

.. _attempt at 1.7 test: https://travis-ci.org/tony/tmuxp/jobs/12348263
.. _kaptan: https://github.com/emre/kaptan
.. _unittest: http://docs.python.org/2/library/unittest.html
.. _BSD-licensed: http://opensource.org/licenses/BSD-2-Clause
