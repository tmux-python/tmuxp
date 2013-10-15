`tmuxp` solves the panes / pains of managing workspaces.

.. image:: https://travis-ci.org/tony/tmuxp.png?branch=master
   :target: https://travis-ci.org/tony/tmuxp

.. image:: https://badge.fury.io/py/tmuxp.png
    :target: http://badge.fury.io/py/tmuxp

tmuxp, a novel approach to managing :term:`tmux(1)` workspaces through
python objects, with configuration loading in JSON, YAML and
:py:obj:`dict` included.

Check out our `Examples`_ and `Quicksart`_.

==============  ==========================================================
tmux support    1.8, 1.9-dev
config support  yaml, json, python dict
Travis          http://travis-ci.org/tony/tmuxp
Docs            http://tmuxp.rtfd.org
API             http://tmuxp.readthedocs.org/en/latest/api.html
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
