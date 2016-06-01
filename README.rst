tmuxp, tmux session manager. built on `libtmux`_.

|pypi| |docs| |build-status| |coverage| |license|

.. image:: https://raw.github.com/tony/tmuxp/master/doc/_static/tmuxp-demo.gif
    :scale: 100%
    :width: 45%
    :align: center

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
       - cd ~/
     panes:
       - shell_command:
           - cd /var/log
           - ls -al | grep \.log
       - pwd
       - pwd
       - pwd

Save as ``mysession.yaml``. And load:

.. code-block:: sh

   $ tmuxp load ./mysession.yaml

`simple`_, `very elaborate`_ config examples

Store configs in (``~/.tmuxp``) or include in your project as
``~/.tmuxp.{yaml,json}``. See `author's tmuxp configs`_ and the
the projects' `tmuxp.yaml`_.

bootstrap project dependencies before loading tmux. See the
`bootstrap_env.py`_ and `before_script`_ example

Load sessions in the background by passing ``-d`` flag

Freeze a tmux session
---------------------

.. code-block:: sh

   $ tmuxp freeze

See more about `freezing tmux`_ sessions.

Docs / Reading material
-----------------------

See the `Quickstart`_.

`Documentation`_ homepage (also in `中文`_)

Want to learn more about tmux itself? Read `The Tao of Tmux`_.

.. _tmuxp on Travis CI: http://travis-ci.org/tony/tmuxp
.. _Documentation: http://tmuxp.rtfd.org/
.. _Source: https://github.com/tony/tmuxp
.. _中文: http://tmuxp-zh.rtfd.org/
.. _before_script: http://tmuxp.readthedocs.io/en/latest/examples.html#bootstrap-project-before-launch
.. _virtualenv: https://virtualenv.readthedocs.io/en/latest/
.. _The Tao of tmux: http://tmuxp.readthedocs.io/en/latest/about_tmux.html
.. _author's tmuxp configs: https://github.com/tony/tmuxp-config
.. _python library: https://tmuxp.readthedocs.io/en/latest/api.html
.. _python API quickstart: https://tmuxp.readthedocs.io/en/latest/quickstart_python.html
.. _tmux(1): http://tmux.sourceforge.net/
.. _tmuxinator: https://github.com/aziz/tmuxinator
.. _teamocil: https://github.com/remiprev/teamocil
.. _Examples: http://tmuxp.readthedocs.io/en/latest/examples.html
.. _freezing tmux: http://tmuxp.readthedocs.io/en/latest/cli.html#freeze-sessions
.. _bootstrap_env.py: https://github.com/tony/tmuxp/blob/master/bootstrap_env.py
.. _travis.yml: http://tmuxp.readthedocs.io/en/latest/developing.html#travis-ci
.. _testing: http://tmuxp.readthedocs.io/en/latest/developing.html#test-runner
.. _python objects: http://tmuxp.readthedocs.io/en/latest/api.html#api
.. _tmuxp.yaml: https://github.com/tony/tmuxp/blob/master/.tmuxp.yaml 
.. _simple: http://tmuxp.readthedocs.io/en/latest/examples.html#short-hand-inline
.. _very elaborate: http://tmuxp.readthedocs.io/en/latest/examples.html#super-advanced-dev-environment
.. _Quickstart: http://tmuxp.readthedocs.io/en/latest/quickstart.html
.. _Commands: http://tmuxp.readthedocs.io/en/latest/cli.html
.. _libtmux: https://github.com/tony/libtmux

Project details
---------------

==============  ==========================================================
tmux support    1.8, 1.9a, 2.0, 2.1, 2.2
python support  2.6, 2.7, >= 3.3
config support  yaml, json, python dict
Source          https://github.com/tony/tmuxp
Docs            http://tmuxp.rtfd.org
API             http://tmuxp.readthedocs.io/en/latest/api.html
Changelog       http://tmuxp.readthedocs.io/en/latest/history.html
Issues          https://github.com/tony/tmuxp/issues
Travis          http://travis-ci.org/tony/tmuxp
Test Coverage   https://coveralls.io/r/tony/tmuxp
pypi            https://pypi.python.org/pypi/tmuxp
Open Hub        https://www.openhub.net/p/tmuxp
License         `BSD`_.
git repo        .. code-block:: bash

                    $ git clone https://github.com/tony/tmuxp.git
install stable  .. code-block:: bash

                    $ sudo pip install tmuxp
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
.. _developing and testing: http://tmuxp.readthedocs.io/en/latest/developing.html

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
