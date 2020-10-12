tmuxp, tmux session manager. built on `libtmux`_.

|pypi| |docs| |build-status| |coverage| |license|

**We need help!** tmuxp is a trusted session manager for tmux. If you
could lend your time to helping answer issues and QA pull requests, please
do! See `issue #290 <https://github.com/tmux-python/tmuxp/issues/290>`__!

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

Projects with *.tmuxp.yaml* or *.tmuxp.json* load via directory:

.. code-block:: sh

    $ tmuxp load path/to/my/project/

Load multiple at once (in bg, offer to attach last):

.. code-block:: sh

    $ tmuxp load mysession ./another/project/ 

Name a session:

.. code-block:: bash

    $ tmxup load -s session_name ./mysession.yaml

`simple`_ and `very elaborate`_ config examples

User-level configurations
-------------------------
tmuxp checks for configs in user directories:

- ``$TMUXP_CONFIGDIR``, if set
- ``$XDG_CONFIG_HOME``, usually *$HOME/.config/tmuxp/*
- ``$HOME/.tmuxp/``

Load your tmuxp config from anywhere by using the filename, assuming
*~/.config/tmuxp/mysession.yaml* (or *.json*):

.. code-block:: sh

    $ tmuxp load mysession

See `author's tmuxp configs`_ and the projects' `tmuxp.yaml`_.

Pre-load hook
-------------
Run custom startup scripts (such as installing project dependencies before
loading tmux. See the `bootstrap_env.py`_ and `before_script`_ example

Load in detached state
----------------------
You can also load sessions in the background by passing ``-d`` flag

Screenshot
----------

.. image:: https://raw.github.com/tmux-python/tmuxp/master/doc/_static/tmuxp-demo.gif
    :scale: 100%
    :width: 45%
    :align: center
 

Freeze a tmux session
---------------------

Snapshot your tmux layout, pane paths, and window/session names. 

.. code-block:: sh

   $ tmuxp freeze session-name

See more about `freezing tmux`_ sessions.


Convert a session file
----------------------

Convert a session file from yaml to json and vice versa.

.. code-block:: sh

   $ tmuxp convert filename

This will prompt you for confirmation and shows you the new file that is going
to be written.


You can auto confirm the prompt. In this case no preview will be shown.

.. code-block:: sh

   $ tmuxp convert -y filename
   $ tmuxp convert --yes filename


Docs / Reading material
-----------------------

See the `Quickstart`_.

`Documentation`_ homepage (also in `中文`_)

Want to learn more about tmux itself? `Read The Tao of Tmux online`_.

.. _tmuxp on Travis CI: http://travis-ci.org/tmux-python/tmuxp
.. _Documentation: http://tmuxp.git-pull.com
.. _Source: https://github.com/tmux-python/tmuxp
.. _中文: http://tmuxp-zh.rtfd.org/
.. _before_script: http://tmuxp.git-pull.com/examples.html#bootstrap-project-before-launch
.. _virtualenv: https://virtualenv.git-pull.com/
.. _Read The Tao of tmux online: http://tmuxp.git-pull.com/about_tmux.html
.. _author's tmuxp configs: https://github.com/tony/tmuxp-config
.. _python library: https://tmuxp.git-pull.com/api.html
.. _python API quickstart: https://tmuxp.git-pull.com/quickstart_python.html
.. _tmux(1): http://tmux.sourceforge.net/
.. _tmuxinator: https://github.com/aziz/tmuxinator
.. _teamocil: https://github.com/remiprev/teamocil
.. _Examples: http://tmuxp.git-pull.com/examples.html
.. _freezing tmux: http://tmuxp.git-pull.com/cli.html#freeze-sessions
.. _bootstrap_env.py: https://github.com/tmux-python/tmuxp/blob/master/bootstrap_env.py
.. _travis.yml: http://tmuxp.git-pull.com/developing.html#travis-ci
.. _testing: http://tmuxp.git-pull.com/developing.html#test-runner
.. _python objects: http://tmuxp.git-pull.com/api.html#api
.. _tmuxp.yaml: https://github.com/tmux-python/tmuxp/blob/master/.tmuxp.yaml 
.. _simple: http://tmuxp.git-pull.com/examples.html#short-hand-inline
.. _very elaborate: http://tmuxp.git-pull.com/examples.html#super-advanced-dev-environment
.. _Quickstart: http://tmuxp.git-pull.com/quickstart.html
.. _Commands: http://tmuxp.git-pull.com/cli.html
.. _libtmux: https://github.com/tmux-python/libtmux
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
- tmux support: 1.8, 1.9a, 2.0, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6
- python support: 2.7, >= 3.3, pypy, pypy3
- Source: https://github.com/tmux-python/tmuxp
- Docs: https://tmuxp.git-pull.com
- API: https://tmuxp.git-pull.com/api.html
- Changelog: https://tmuxp.git-pull.com/history.html
- Issues: https://github.com/tmux-python/tmuxp/issues
- Test Coverage: https://codecov.io/gh/tmux-python/tmuxp
- pypi: https://pypi.python.org/pypi/tmuxp
- Open Hub: https://www.openhub.net/p/tmuxp-python
- License: `MIT`_.

.. _MIT: http://opensource.org/licenses/MIT
.. _developing and testing: http://tmuxp.git-pull.com/developing.html
.. _Amazon Kindle: http://amzn.to/2gPfRhC

.. |pypi| image:: https://img.shields.io/pypi/v/tmuxp.svg
    :alt: Python Package
    :target: http://badge.fury.io/py/tmuxp

.. |docs| image:: https://github.com/tmux-python/tmuxp/workflows/Publish%20Docs/badge.svg
   :alt: Docs
   :target: https://github.com/tmux-python/tmuxp/actions?query=workflow%3A"Publish+Docs"

.. |build-status| image:: https://img.shields.io/travis/tmux-python/tmuxp.svg
   :alt: Build Status
   :target: https://travis-ci.org/tmux-python/tmuxp

.. |coverage| image:: https://codecov.io/gh/tmux-python/tmuxp/branch/master/graph/badge.svg
    :alt: Code Coverage
    :target: https://codecov.io/gh/tmux-python/tmuxp

.. |license| image:: https://img.shields.io/github/license/tmux-python/tmuxp.svg
    :alt: License 
