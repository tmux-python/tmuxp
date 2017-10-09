tmuxp, tmux session manager. built on `libtmux`_.

|pypi| |docs| |build-status| |coverage| |license|

**New to tmux?** `The Tao of tmux <https://leanpub.com/the-tao-of-tmux>`_ is
available on Leanpub and `Amazon Kindle`_. Read and browse the book for free
`on the web`_.

Installation
------------

.. code-block:: shell

   $ pip install --user tmuxp

Load a tmux session
-------------------

Load tmux sessions via json and YAML, `tmuxinator`_ and
`teamocil`_ style.

.. code-block:: yaml

   session_name: 4-pane-split
   windows:
   - window_name: dev window
     layout: tiled
     shell_command_before:
       - cd ~/                    # run as a first command in all panes
     panes:
       - shell_command:           # pane no. 1
           - cd /var/log          # run multiple commands in this pane
           - ls -al | grep \.log
       - echo second pane         # pane no. 2
       - echo third pane          # pane no. 3
       - echo forth pane          # pane no. 4

Save as *mysession.yaml*, and load:

.. code-block:: sh

   $ tmuxp load ./mysession.yaml

Sessions in *~/.tmuxp/* can use names:

.. code-block:: sh

    $ tmuxp load mysession

Projects with *.tmuxp.yaml* or *.tmuxp.json* load via directory:

.. code-block:: sh

    $ tmuxp load path/to/my/project/

Load multiple at once (in bg, offer to attach last):

.. code-block:: sh

    $ tmuxp load mysession ./another/project/ 

`simple`_ and `very elaborate`_ config examples

Store configs in (*~/.tmuxp*) or include in your project as
*~/.tmuxp.{yaml,json}*. See `author's tmuxp configs`_ and the
the projects' `tmuxp.yaml`_.

Run custom startup scripts (such as installing project dependencies before
loading tmux. See the `bootstrap_env.py`_ and `before_script`_ example

You can also load sessions in the background by passing ``-d`` flag

.. image:: https://raw.github.com/tony/tmuxp/master/doc/_static/tmuxp-demo.gif
    :scale: 100%
    :width: 45%
    :align: center
 

Freeze a tmux session
---------------------

Snapshot your tmux layout, pane paths, and window/session names. 

.. code-block:: sh

   $ tmuxp freeze session-name

See more about `freezing tmux`_ sessions.

Docs / Reading material
-----------------------

See the `Quickstart`_.

`Documentation`_ homepage (also in `中文`_)

Want to learn more about tmux itself? `Read The Tao of Tmux online`_.

.. _tmuxp on Travis CI: http://travis-ci.org/tony/tmuxp
.. _Documentation: http://tmuxp.git-pull.com
.. _Source: https://github.com/tony/tmuxp
.. _中文: http://tmuxp-zh.rtfd.org/
.. _before_script: http://tmuxp.git-pull.com/en/latest/examples.html#bootstrap-project-before-launch
.. _virtualenv: https://virtualenv.git-pull.com/en/latest/
.. _Read The Tao of tmux online: http://tmuxp.git-pull.com/en/latest/about_tmux.html
.. _author's tmuxp configs: https://github.com/tony/tmuxp-config
.. _python library: https://tmuxp.git-pull.com/en/latest/api.html
.. _python API quickstart: https://tmuxp.git-pull.com/en/latest/quickstart_python.html
.. _tmux(1): http://tmux.sourceforge.net/
.. _tmuxinator: https://github.com/aziz/tmuxinator
.. _teamocil: https://github.com/remiprev/teamocil
.. _Examples: http://tmuxp.git-pull.com/en/latest/examples.html
.. _freezing tmux: http://tmuxp.git-pull.com/en/latest/cli.html#freeze-sessions
.. _bootstrap_env.py: https://github.com/tony/tmuxp/blob/master/bootstrap_env.py
.. _travis.yml: http://tmuxp.git-pull.com/en/latest/developing.html#travis-ci
.. _testing: http://tmuxp.git-pull.com/en/latest/developing.html#test-runner
.. _python objects: http://tmuxp.git-pull.com/en/latest/api.html#api
.. _tmuxp.yaml: https://github.com/tony/tmuxp/blob/master/.tmuxp.yaml 
.. _simple: http://tmuxp.git-pull.com/en/latest/examples.html#short-hand-inline
.. _very elaborate: http://tmuxp.git-pull.com/en/latest/examples.html#super-advanced-dev-environment
.. _Quickstart: http://tmuxp.git-pull.com/en/latest/quickstart.html
.. _Commands: http://tmuxp.git-pull.com/en/latest/cli.html
.. _libtmux: https://github.com/tony/libtmux
.. _on the web: https://leanpub.com/the-tao-of-tmux/read

Donations
---------

Your donations fund development of new features, testing and support.
Your money will go directly to maintenance and development of the project.
If you are an individual, feel free to give whatever feels right for the
value you get out of the project.

See donation options at https://git-pull.com/support.html.

Project details
---------------

==============  ==========================================================
tmux support    1.8, 1.9a, 2.0, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6
python support  2.7, >= 3.3, pypy, pypy3
config support  yaml, json, python dict
Source          https://github.com/tony/tmuxp
Docs            http://tmuxp.git-pull.com
API             http://tmuxp.git-pull.com/en/latest/api.html
Changelog       http://tmuxp.git-pull.com/en/latest/history.html
Issues          https://github.com/tony/tmuxp/issues
Travis          http://travis-ci.org/tony/tmuxp
Test Coverage   https://codecov.io/gh/tony/tmuxp
pypi            https://pypi.python.org/pypi/tmuxp
Open Hub        https://www.openhub.net/p/tmuxp
License         `BSD`_.
git repo        .. code-block:: bash

                    $ git clone https://github.com/tony/tmuxp.git
install stable  .. code-block:: bash

                    $ pip install --user tmuxp
install dev     .. code-block:: bash

                    $ git clone https://github.com/tony/tmuxp.git tmuxp
                    $ cd ./tmuxp
                    $ virtualenv .venv
                    $ source .venv/bin/activate
                    $ pip install -e .

                See the `developing and testing`_ page in the docs for
                more.
tests           .. code-block:: bash

                    $ make test
==============  ==========================================================

.. _BSD: http://opensource.org/licenses/BSD-3-Clause
.. _developing and testing: http://tmuxp.git-pull.com/en/latest/developing.html
.. _Amazon Kindle: http://amzn.to/2gPfRhC

.. |pypi| image:: https://img.shields.io/pypi/v/tmuxp.svg
    :alt: Python Package
    :target: http://badge.fury.io/py/tmuxp

.. |build-status| image:: https://img.shields.io/travis/tony/tmuxp.svg
   :alt: Build Status
   :target: https://travis-ci.org/tony/tmuxp

.. |coverage| image:: https://codecov.io/gh/tony/tmuxp/branch/master/graph/badge.svg
    :alt: Code Coverage
    :target: https://codecov.io/gh/tony/tmuxp

.. |license| image:: https://img.shields.io/github/license/tony/tmuxp.svg
    :alt: License 

.. |docs| image:: https://readthedocs.org/projects/tmuxp/badge/?version=latest
    :alt: Documentation Status
    :scale: 100%
    :target: https://readthedocs.org/projects/tmuxp/
