`tmuxp` solves the panes / pains of managing workspaces.

.. image:: https://travis-ci.org/tony/tmuxp.png?branch=master
   :target: https://travis-ci.org/tony/tmuxp

.. image:: https://badge.fury.io/py/tmuxp.png
    :target: http://badge.fury.io/py/tmuxp

.. figure:: https://raw.github.com/tony/tmuxp/master/doc/_static/tmuxp-dev-screenshot.png
    :scale: 100%
    :width: 65%
    :align: center

Open to testers
---------------

tmuxp is still **alpha** code and needs a few more weeks until stable.
See the `Issues tracker`_ to see known issues and for any other concerns.


tmux bash completion
""""""""""""""""""""

.. code-block:: bash

    $ tmuxp attach-session<tab>
    # tmuxp will also automatically ``switch-client`` if you are already
    # inside a tmux client.
    $ tmuxp kill-session<tab>
    $ tmuxp load<tab>
    # load a session configuration with windows, panes, autocommands from
    # a YAML or JSON file.

See: `bash completion`_

load tmux sessions from yaml and json
"""""""""""""""""""""""""""""""""""""

.. code-block:: bash

    $ tmuxp load .

Load from ``~/.tmuxp.yaml`` or ``~/.tmuxp.json`` in current directory.

.. code-block:: bash

    $ tmuxp load myconfig.yaml

Load ``myconfig.yaml``, checking current directory, then
``$HOME/.tmuxp/myconfig.yaml``.

tmuxp will prompt you if session is already running, press ``[Enter]``
to attach the session automatically.

If you load a config from *inside* tmux, tmuxp will offer to attach it
for you.

See: `Examples`_

Install
"""""""

- install ``tmux``, at least version **1.8**
- libyaml is installed for your distribution.

Install ``tmuxp``:

.. code-block:: bash

    $ pip install tmuxp
    
``$ mkdir ~/.tmuxp`` and make a file ``~/.tmuxp/test.yaml``.

.. code-block:: yaml

    session_name: my session
    windows:
    - window_name: my test window
      shell_command_before: cd ~
      panes:
      - pwd
      - pwd

With ``tmuxp``:

.. code-block:: bash

    $ tmuxp load test.yaml

See also: `Quickstart`_

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
.. _ORM: http://tmuxp.readthedocs.org/en/latest/quickstart.html#tmux-orm
.. _tmux(1): http://tmux.sourceforge.net/
.. _Issues tracker: https://github.com/tony/tmuxp/issues
.. _python dict: http://docs.python.org/2/library/stdtypes.html#dict
