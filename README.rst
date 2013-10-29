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

Install
"""""""

- install ``tmux``, at least version **1.8**
- libyaml is installed for your distribution.

Install ``tmuxp``:

.. code-block:: bash

    $ pip install tmuxp
    

See: `Quickstart`_

CLI Commands
""""""""""""

========================== ==============================================
 ``tmuxp attach-session``  ``<session_name>``
                           tmuxp uses ``switch-client`` if already inside
                           tmux client.
 ``tmuxp kill-session``    ``<session name>``.
 ``tmuxp load``            ``<file>``. Load a workspace yaml / json file.
                           If session already made, will offer to attach.
 ``tmuxp convert``         ``<file>``. Convert session yaml / json.
 ``tmuxp import``          ``[teamocil | tmuxinator]`` ``<file>`` import
                           a `teamocil`_ or `tmuxinator`_ config.
========================== ==============================================

Bash completion
"""""""""""""""

For bash, ``.bashrc``:

.. code-block:: bash

    $ source tmuxp.bash

For tcsh, ``.tcshrc``:

.. code-block:: bash

    $ complete tmuxp 'p/*/`tmuxp.tcsh`/'

For zsh, ``.zshrc``:

.. code-block:: bash

    $ source tmuxp.zsh

See `installing bash completion`_ to get bash, zsh and tcsh completion
working on your machine.

Mini Quickstart
"""""""""""""""

See the full `Quickstart`_ in the documentation.

Load from ``~/.tmuxp.yaml`` or ``~/.tmuxp.json`` in current directory.

.. code-block:: bash

    $ tmuxp load .

Load ``myconfig.yaml`` from ``~/.tmuxp``

.. code-block:: bash

    $ tmuxp load myconfig.yaml

Load a relative or full config file (bash complete supports this too)

.. code-block:: bash

    $ tmuxp load ./myconfig.yaml
    $ tmuxp load ../myconfig.yaml
    $ tmuxp load /var/www/mywebproject/myconfig.yaml

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

See: `Examples`_

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
.. _installing bash completion: http://tmuxp.readthedocs.org/en/latest/quickstart.html#bash-completion
.. _Developing and Testing: http://tmuxp.readthedocs.org/en/latest/developing.html
.. _tmuxinator: https://github.com/aziz/tmuxinator
.. _teamocil: https://github.com/remiprev/teamocil
.. _abstraction layer: http://en.wikipedia.org/wiki/Abstraction_layer
.. _ORM: http://tmuxp.readthedocs.org/en/latest/quickstart.html#tmux-orm
.. _tmux(1): http://tmux.sourceforge.net/
.. _Issues tracker: https://github.com/tony/tmuxp/issues
.. _python dict: http://docs.python.org/2/library/stdtypes.html#dict
