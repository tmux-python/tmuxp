`tmuxp` solves the panes / pains of managing workspaces.

.. image:: https://travis-ci.org/tony/tmuxp.png?branch=master
   :target: https://travis-ci.org/tony/tmuxp

.. image:: https://badge.fury.io/py/tmuxp.png
    :target: http://badge.fury.io/py/tmuxp

tmuxp, a novel approach to managing `tmux(1)`_ workspaces through
python objects. Features:

- resume session from config file, if already built.
- load configs + build workspace + switching to new session even when
  inside tmux
- bash / zsh / tcsh completion
- JSON, YAML and py dict config
- Support for pre-commands with ``shell_command_before`` to load
  virtualenv / rvm / any other commands
- Load sessions from directory with ``$ tmuxp .`` to load ``.tmuxp.py`` /
  ``.tmuxp.yaml`` / ``.tmuxp.json`` and  ``$ tmuxp configfile.yaml`` when
  inside same directory.
- Have a feature suggestion, bug,  or need help? `Post an issue`_.

.. figure:: https://raw.github.com/tony/tmuxp/master/doc/_static/tmuxp-dev-screenshot.png
    :scale: 100%
    :width: 65%
    :align: center

tmuxp works in 3 ways:

- a pythonic `abstraction layer`_ on top of tmux' CLI commands
- an `ORM`_ that internally orchestrates relations between servers,
  sessions, windows and panes for good and evil purposes.
- CLI tmux session manager, similar to `teamocil`_ and `tmuxinator`_, with
  support for YAML, JSON and python dicts.

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

Check out our `Examples`_, `Quickstart`_ and `bash completion`_ support.

Advanced tmux workflow:

.. code-block:: yaml

    session_name: tmuxp
    windows:
    - window_name: tmuxp
      layout: main-horizontal
      options:
        main-pane-height: 50
      start_directory: ./
      shell_command_before:
        - '[ -d .env -a -f .env/bin/activate ] && source .env/bin/activate || virtualenv .env'
      panes:
      - shell_command: 
        - vim
        - :Ex
        focus: true
      - shell_command: 
        - echo hi
      - shell_command: 
        - '[ -d .env -a -f .env/bin/activate ] || virtualenv .env'
        - command -v tmuxp >/dev/null 2>&1 || { pip install -e .; }
        - command -v watching_testrunner >/dev/null 2>&1 || { pip install watching_testrunner; }
        - watching_testrunner --basepath ./ --pattern="*.py" python run_tests.py
    - window_name: docs
      layout: main-horizontal
      options:
        main-pane-height: 50
      start_directory: ./
      automatic_rename: true
      shell_command_before: 
        - '[ -d .env -a -f .env/bin/activate ] && source .env/bin/activate || virtualenv .env'
        - command -v tmuxp >/dev/null 2>&1 || { pip install -e .; }
        - cd ./doc
      panes:
      - shell_command:
        - vim
        focus: true
      - pwd
      - echo 'docs built to <http://0.0.0.0:8000/_build/html>'; python -m SimpleHTTPServer
      - shell_command:
        - command -v sphinx-quickstart >/dev/null 2>&1 || { pip install -r requirements.pip; }
        - command -v watching_testrunner >/dev/null 2>&1 || { pip install watching_testrunner; }
        - watching_testrunner --basepath ./ --pattern="*.rst" 'make html'

see this in the `Developing and Testing`_ documentation page.

==============  ==========================================================
tmux support    1.8, 1.9-dev
config support  yaml, json, python dict
Travis          http://travis-ci.org/tony/tmuxp
Docs            http://tmuxp.rtfd.org
API             http://tmuxp.readthedocs.org/en/latest/api.html
Changelog       http://tmuxp.readthedocs.org/en/latest/changes.html
Issues          https://github.com/tony/tmuxp/issues
Source          https://github.com/tony/tmuxp
pypi            https://pypi.python.org/pypi/tmuxp
License         `BSD`_.
git repo        .. code-block:: bash

                    $ git clone https://github.com/tony/tmuxp.git
install dev     .. code-block:: bash

                    $ git clone https://github.com/tony/tmuxp.git tmuxp
                    $ cd ./tmuxp
                    $ virtualenv .env
                    $ source .env/bin/activate
                    $ pip install -e .

                See the `developing and testing`_ page in the docs for
                more.
tests           .. code-block:: bash

                    $ python ./run_tests.py
==============  ==========================================================

.. _BSD: http://opensource.org/licenses/BSD-3-Clause
.. _developing and testing: http://tmuxp.readthedocs.org/en/latest/developing.html
.. _Examples: http://tmuxp.readthedocs.org/en/latest/examples.html
.. _Quickstart: http://tmuxp.readthedocs.org/en/latest/quickstart.html
.. _bash completion: http://tmuxp.readthedocs.org/en/latest/quickstart.html#bash-completion
.. _Developing and Testing: http://tmuxp.readthedocs.org/en/latest/developing.html
.. _tmuxinator: https://github.com/aziz/tmuxinator
.. _teamocil: https://github.com/remiprev/teamocil
.. _abstraction layer: http://en.wikipedia.org/wiki/Abstraction_layer
.. _ORM: http://en.wikipedia.org/wiki/Object-relational_mapping
.. _tmux(1): http://tmux.sourceforge.net/
.. _Post an issue: https://github.com/tony/tmuxp/issues
