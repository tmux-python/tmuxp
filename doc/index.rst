tmuxp
=====

.. image:: _static/tmuxp-dev-screenshot.png
    :scale: 35%
    :width: 100%
    :align: right


tmuxp, a novel approach to manage `tmux(1)`_ (>= 1.8) workspaces through
`python objects`_.

- Basic support for `freezing live sessions`_
- `importing`_ from `teamocil`_ and `tmuxinator`_.
- JSON or YAML for `simple`_ or `very elaborate`_ configurations.
- `bash, zsh and tcsh`_ completion.
- Unit tested against against live tmux (1.8 and git). See `travis.yml`_
  file and `testing`_ page.
- Documented Examples, Internals.
- and `much, much more`_

Ready to begin? See the `Quickstart`_.

More tweaks:

- Load + switch to new session from inside tmux.
- Resume session if config loaded.
- Pre-commands virtualenv / rvm / any other commands.
- Load config from anywhere `$ tmuxp load /full/file/path.json`.

.. _bash, zsh, and tcsh: http://tmuxp.readthedocs.org/en/latest/quickstart.html#bash-completion

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
