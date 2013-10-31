.. _cli:

======================
Command Line Interface
======================

.. _cli_freeze:

Freeze sessions
"""""""""""""""

.. code-block:: bash

    $ tmuxp freeze <session-name>

Tmuxp will offer to convert file to ``.json`` or ``.yaml``.

.. _cli_load:

Load session
""""""""""""

Keep your configs in ``$HOME/.tmuxp`` for easy access and detection by
:ref:`bash_completion`.

Files also may be loaded by absolute path.

.. code-block:: bash

    $ tmuxp load <filename>

Files named ``.tmuxp.yaml`` or ``.tmuxp.json`` in the current working
directory may be loaded with:

.. code-block:: bash

    $ tmuxp load .

Import
""""""

.. _import_teamocil:

From teamocil
'''''''''''''

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

.. code-block:: bash

    $ tmuxp convert <filename>

tmuxp automatically will prompt to convert ``.yaml`` to ``.json`` and
``.json`` to  ``.yaml``.

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
