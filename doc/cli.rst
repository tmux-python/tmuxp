.. _cli:

======================
Command Line Interface
======================

.. _import_teamocil:

Freeze sessions
"""""""""""""""

.. code-block:: bash

    $ tmuxp freeze <filename>

Tmuxp will offer to convert file to ``.json`` or ``.yaml``.

Import
""""""

From teamocil
'''''''''''''

.. _import_teamocil:

.. code-block:: bash

    $ tmuxp import teamocil <filename>

.. _import_tmuxinator:

From tmuxinator
'''''''''''''''

.. code-block:: bash

    $ tmuxp import tmuxinator <filename>

.. _convert_config:

Convert between YAML and JSON
"""""""""""""""""""""""""""""

.. _bash_completion:

    $ tmuxp convert <filename>

tmuxp automatically will prompt to convert ``.yaml`` to ``.json`` and
``.json`` to  ``.yaml``.

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
