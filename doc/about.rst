.. _about:

===========
About tmuxp
===========

For current tmux user
---------------------

tmuxp helps you manage your text-based workspaces. Its BSD licensed,
modelled after tmux's ``commands`` and ``formats``.

For current teamocil / tmuxinator / etc. user
---------------------------------------------

- tmuxp requires python 2.7 on your system.
- the configuration format is slightly different.
- tmuxp allows configs in YAML, JSON, INI and :py:class:`dict` format.

For pythonistas
---------------

tmuxp is an abstraction of :term:`tmux(1)` into python objects.

Uses `kaptan`_ for
configuration.

`unittest`_ for tests. Tested in python 2.7.  You can read our :ref:`api`
documentation for more.

License
-------

tmuxp is `BSD-licensed`_.

Source
------

Code can be found at VCS http://github.com/tony/tmuxp.

Compatibility
-------------

Currently tmuxp is tested with 1.8 and above. It is recommended to update
to the latest version. If there is enough demand, support can be added
to support older versions.

1.7 and below issues:

tmuxp relies on the ``-P`` option to print out session information when
``new-session`` is called (see `attempt at 1.7 test`_).

.. _attempt at 1.7 test: https://travis-ci.org/tony/tmuxp/jobs/12348263
.. _kaptan: https://github.com/emre/kaptan
.. _unittest: http://docs.python.org/2/library/unittest.html
.. _BSD-licensed: http://opensource.org/licenses/BSD-2-Clause


.. todo::

    =========
    Sort this
    =========

    Similarities to Tmux and Pythonics
    ----------------------------------

    tmuxp is was built in the spirit of understanding how tmux operates
    and how python objects and tools can abstract the API's in a pleasant way.

    tmuxp uses the identify ``FORMATTERS`` used by tmux, you can see
    them inside of http://sourceforge.net/p/tmux/tmux-code/ci/master/tree/format.c.

    In this, I will also begin documenting the API.

    the use of:

    Session
    Session.new_window() - returns a new Window object bound to the session,
    also uses ``tmux new-window``.
    Session.new_session() - class method - returns a new Session object.

    Differences from tmux
    ---------------------

    Because this is a python abstraction and flags like ``start-directory``
    have dashes (-) replaced with underscores (_).

    interesting observations
    ------------------------

    How is tmuxp able to keep references to panes, windows and sessions?

        Tmux has unique ID's for sessions, windows and panes.

        panes use ``%``, such as ``%1234``

        windows use ``@``, such as ``@2345``

        sessions use ``$``, for money, such as ``$``

    How is tmuxp able to handle windows with no names?

        Tmux provides ``window_id`` as a unique identifier.

    What is a {pane,window}_index vs a {pane,window,session}_id?

        Pane index refers to the order of a pane on the screen.

        Window index refers to the # of the pane in the session.

    Design decisions in tmuxp
    -------------------------

    placeholder

    Reference
    ---------

    + tmux docs http://www.openbsd.org/cgi-bin/man.cgi?query=tmux&sektion=1
    + tmux source code http://sourceforge.net/p/tmux/tmux-code/ci/master/tree/
