.. _cli:

======================
Command Line Interface
======================

.. _bash_completion:

Bash completion
---------------

For bash, ``.bashrc``:

.. code-block:: bash

    $ source tmuxp.bash

For tcsh, ``.tcshrc``:

.. code-block:: bash

    $ complete tmuxp 'p/*/`tmuxp.tcsh`/'

For zsh, ``.zshrc``:

.. code-block:: bash

    $ source tmuxp.zsh

.. _commands:


.. _cli_freeze:

Freeze sessions
---------------

.. argparse::
    :module: tmuxp.cli
    :func: get_parser
    :prog: tmuxp
    :path: freeze


    You can save the state of your tmux session by freezing it.

    Tmuxp will offer to save your session state to ``.json`` or ``.yaml``.

.. _cli_load:

Load session
------------

.. argparse::
    :module: tmuxp.cli
    :func: get_parser
    :prog: tmuxp
    :path: load

    Keep your configs in ``$HOME/.tmuxp`` for easy access and detection by
    :ref:`bash_completion`.

    Files also may be loaded by absolute path.

    .. code-block:: bash

        $ tmuxp load <filename>

    Files named ``.tmuxp.yaml`` or ``.tmuxp.json`` in the current working
    directory may be loaded with:

    .. code-block:: bash

        $ tmuxp load .

    Multiple sessions can be loaded at once. The first ones will be created
    without being attached. The last one will be attached if there is no
    ``-d`` flag on the command line.

    .. code-block:: bash

        $ tmuxp load <filename1> <filename2> ...

.. _cli_import:

Import
------

.. _import_teamocil:

From teamocil
~~~~~~~~~~~~~

.. argparse::
    :module: tmuxp.cli
    :func: get_parser
    :prog: tmuxp
    :path: import teamocil

.. _import_tmuxinator:

From tmuxinator
~~~~~~~~~~~~~~~

.. argparse::
    :module: tmuxp.cli
    :func: get_parser
    :prog: tmuxp
    :path: import tmuxinator

.. _convert_config:

Convert between YAML and JSON
-----------------------------

.. argparse::
    :module: tmuxp.cli
    :func: get_parser
    :prog: tmuxp
    :path: convert


    tmuxp automatically will prompt to convert ``.yaml`` to ``.json`` and
    ``.json`` to  ``.yaml``.

Other commands
--------------

.. argparse::
    :module: tmuxp.cli
    :func: get_parser
    :prog: tmuxp
    :path: kill-session

.. argparse::
    :module: tmuxp.cli
    :func: get_parser
    :prog: tmuxp
    :path: attach-session
