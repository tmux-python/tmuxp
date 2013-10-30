tmuxp
=====

.. image:: _static/tmuxp-dev-screenshot.png
    :scale: 35%
    :width: 100%
    :align: right

tmuxp, a novel approach to managing `tmux(1)`_ workspaces through
python objects. Features:

- Load + switch to new session from inside tmux.
- :ref:`bash / zsh / tcsh completion <bash_completion>`.
- JSON, YAML and `python dict`_ configuration.
- Support for pre-commands with ``shell_command_before`` to load
  virtualenv / rvm / any other commands.
- Session resuming from config file if already running.
- Per-project tmux sessions, load directly from config file.
  `` $ tmuxp load /full/file/path.json ``
- uses tmux 1.8's ``pane_id``, ``window_id`` and ``session_id`` to build
  create python objects to build workspaces with the freshest data.
- (experimental) Import configs from `teamocil`_ and `tmuxinator`_.
- (experimental) Freezing sessions.

tmuxp works in 3 ways:

- a pythonic `abstraction layer`_ on top of tmux' CLI commands
- an `ORM`_ that internally orchestrates relations between servers,
  sessions, windows and panes for good and evil purposes.
- CLI tmux session manager, similar to `teamocil`_ and `tmuxinator`_, with
  support for loading YAML, JSON and python dicts.

Get started
-----------

Get the prerequisites:

1. installed ``tmux``, at least version **1.8**
2. libyaml is installed for your distribution.

To install ``tmuxp``:

.. code-block:: bash

    $ pip install tmuxp
    
``$ mkdir ~/.tmuxp`` and make a file ``~/.tmuxp/test.yaml``.

.. code-block:: yaml

    session_name: 2-pane-vertical
    windows:
      - window_name: my test window
        panes:
          - pwd
          - pwd

.. code-block:: bash

    $ tmuxp load test.yaml

or ``~/.tmuxp/test.json``:

.. code-block:: json

    {
      "windows": [
        {
          "panes": [
            "pwd", 
            "pwd"
          ], 
          "window_name": "my test window"
        }
      ], 
      "session_name": "2-pane-vertical"
    }

.. code-block:: bash

    $ tmuxp load test.json

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
.. _Issues tracker: https://github.com/tony/tmuxp/issues
.. _python dict: http://docs.python.org/2/library/stdtypes.html#dict
