.. _cli:

======================
Command Line Interface
======================

.. _bash_completion:

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


.. commands::

Commands
""""""""

.. argparse::
    :module: tmuxp.cli
    :func: get_parser
    :prog: tmuxp
