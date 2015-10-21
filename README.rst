tmuxp, a novel approach to manage `tmux(1)`_ (>= 1.8) workspaces through
`python objects`_, JSON or YAML.

|pypi| |docs| |build-status| |coverage| |license|

.. image:: https://raw.github.com/tony/tmuxp/master/doc/_static/tmuxp-demo.gif
    :scale: 100%
    :width: 45%
    :align: center

- Basic support for `freezing live sessions`_.
- `Importing`_ from `teamocil`_ and `tmuxinator`_.
- JSON or YAML for `simple`_ or `very elaborate`_ configurations.
- `bash, zsh and tcsh`_ completion.
- Unit tested against live tmux (1.8 and git). See `travis.yml`_
  file, `tmuxp on Travis CI`_ and `testing`_ page.
- `Documentation`_ (also in `中文`_), `Examples`_, `Source`_, 
  `Commands`_, `Internals`_.
- and `much, much more`_.

Ready to begin? See the `Quickstart`_.

.. _tmuxp on Travis CI: http://travis-ci.org/tony/tmuxp
.. _Documentation: http://tmuxp.rtfd.org/
.. _Source: https://github.com/tony/tmuxp
.. _中文: http://tmuxp-zh.rtfd.org/
.. _tmux(1): http://tmux.sourceforge.net/
.. _tmuxinator: https://github.com/aziz/tmuxinator
.. _teamocil: https://github.com/remiprev/teamocil
.. _Examples: http://tmuxp.readthedocs.org/en/latest/examples.html
.. _freezing live sessions: http://tmuxp.readthedocs.org/en/latest/cli.html#freeze-sessions
.. _Importing: http://tmuxp.readthedocs.org/en/latest/cli.html#import
.. _travis.yml: http://tmuxp.readthedocs.org/en/latest/developing.html#travis-ci
.. _testing: http://tmuxp.readthedocs.org/en/latest/developing.html#test-runner
.. _python objects: http://tmuxp.readthedocs.org/en/latest/api.html#api
.. _simple: http://tmuxp.readthedocs.org/en/latest/examples.html#short-hand-inline
.. _very elaborate: http://tmuxp.readthedocs.org/en/latest/examples.html#super-advanced-dev-environment
.. _bash, zsh and tcsh: http://tmuxp.readthedocs.org/en/latest/cli.html#bash-completion
.. _much, much more: http://tmuxp.readthedocs.org/en/latest/about.html#minor-tweaks
.. _Quickstart: http://tmuxp.readthedocs.org/en/latest/quickstart.html
.. _Internals: http://tmuxp.readthedocs.org/en/latest/internals.html
.. _Commands: http://tmuxp.readthedocs.org/en/latest/cli.html

Project details
---------------

==============  ==========================================================
tmux support    1.8, 1.9a, 2.0, 2.1
python support  2.6, 2.7, >= 3.3
config support  yaml, json, python dict
Source          https://github.com/tony/tmuxp
Docs            http://tmuxp.rtfd.org
API             http://tmuxp.readthedocs.org/en/latest/api.html
Changelog       http://tmuxp.readthedocs.org/en/latest/history.html
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
                    $ virtualenv .env
                    $ source .env/bin/activate
                    $ pip install -e .

                See the `developing and testing`_ page in the docs for
                more.
tests           .. code-block:: bash

                    $ python ./run-tests.py
==============  ==========================================================

.. _BSD: http://opensource.org/licenses/BSD-3-Clause
.. _developing and testing: http://tmuxp.readthedocs.org/en/latest/developing.html
.. _installing bash completion: http://tmuxp.readthedocs.org/en/latest/quickstart.html#bash-completion
.. _Developing and Testing: http://tmuxp.readthedocs.org/en/latest/developing.html
.. _Issues tracker: https://github.com/tony/tmuxp/issues

.. |pypi| image:: https://img.shields.io/pypi/v/tmuxp.svg
    :alt: Python Package
    :target: http://badge.fury.io/py/tmuxp

.. |build-status| image:: https://img.shields.io/travis/tony/tmuxp.svg
   :alt: Build Status
   :target: https://travis-ci.org/tony/tmuxp

.. |coverage| image:: https://img.shields.io/coveralls/tony/tmuxp.svg
    :alt: Code Coverage
    :target: https://coveralls.io/r/tony/tmuxp?branch=master
    
.. |license| image:: https://img.shields.io/github/license/tony/tmuxp.svg
    :alt: License 

.. |docs| image:: https://readthedocs.org/projects/tmuxp/badge/?version=latest
    :alt: Documentation Status
    :scale: 100%
    :target: https://readthedocs.org/projects/tmuxp/
