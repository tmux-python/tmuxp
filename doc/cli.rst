.. _cli:

======================
Command Line Interface
======================

.. _import_teamocil:

Freeze sessions
"""""""""""""""

.. code-block:: bash

    $ tmuxp freeze <filename>

Import from teamocil
""""""""""""""""""""

.. _import_teamocil:

.. code-block:: bash

    $ tmuxp import teamocil <filename>

.. _import_tmuxinator:

Import from tmuxinator
""""""""""""""""""""""

.. code-block:: bash

    $ tmuxp import tmuxinator <filename>

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
