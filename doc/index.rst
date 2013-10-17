tmuxp
=====

.. image:: _static/tmuxp-dev-screenshot.png
    :scale: 35%
    :width: 100%
    :align: right

tmuxp, a novel approach to managing `tmux(1)`_ workspaces through
python objects. Features:

- resume session from config file, if already built.
- load configs + build workspace + switching to new session even when
  inside tmux
- bash / zsh / tcsh completion
- JSON, YAML and :py:obj:`dict` config
- Support for pre-commands with ``shell_command_before`` to load
  virtualenv / rvm / any other commands
- Load sessions from directory with ``$ tmuxp .`` to load ``.tmuxp.py`` /
  ``.tmuxp.yaml`` / ``.tmuxp.json`` and  ``$ tmuxp configfile.yaml`` when
  inside same directory.

tmuxp works in 3 ways:

- a pythonic `abstraction layer`_ on top of tmux' CLI commands
- an `ORM`_ that internally orchestrates relations between servers,
  sessions, windows and panes for good and evil purposes.
- CLI tmux session manager, similar to `teamocil`_ and `tmuxinator`_, with
  support for loading YAML, JSON and python dicts.
- Have a feature suggestion, bug,  or need help? `Post an issue`_.

Get started now, make sure:

1.) have ``tmux`` installed.
2.) is at least version 1.8 ``$ tmux -V``.
3.) libyaml is installed for your distribution.

.. code-block:: bash

    $ pip install tmuxp
    
``$ mkdir ~/.tmuxp`` and make a file ``~/.tmuxp/test.yaml``.

.. code-block:: yaml

    session_name: my session
    windows:
    - window_name: my test window
        panes:
        - bash
        - bash

Now with ``tmuxp``:

.. code-block:: bash

    $ tmuxp test.yaml

Jump right in: See `Examples`_, `Quickstart`_ and `bash completion`_
support.

Explore:

.. toctree::
    :maxdepth: 2

    about
    about_tmux
    quickstart
    examples
    orm_al
    developing
    api
    glossary
    changes

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _tmuxinator: https://github.com/aziz/tmuxinator
.. _teamocil: https://github.com/remiprev/teamocil
.. _abstraction layer: http://en.wikipedia.org/wiki/Abstraction_layer
.. _ORM: http://en.wikipedia.org/wiki/Object-relational_mapping
.. _Examples: http://tmuxp.readthedocs.org/en/latest/examples.html
.. _Quickstart: http://tmuxp.readthedocs.org/en/latest/quickstart.html
.. _bash completion: http://tmuxp.readthedocs.org/en/latest/quickstart.html#bash-completion
.. _tmux(1): http://tmux.sourceforge.net/
.. _Post an issue: https://github.com/tony/tmuxp/issues
