.. _cli:

======================
Command Line Interface
======================

.. _commands:

.. _cli_freeze:

Freeze sessions
---------------

::

    tmuxp freeze <session_name>

You can save the state of your tmux session by freezing it.

Tmuxp will offer to save your session state to ``.json`` or ``.yaml``.

.. _cli_load:

Load session
------------

::

    # path to folder with .tmuxp.{yaml,yml,json}
    tmuxp load .
    tmuxp load ../
    tmuxp load path/to/folder/
    tmuxp load /path/to/folder/

    # name of the config, assume $HOME/.tmuxp/myconfig.yaml
    tmuxp load myconfig

    # direct path to json/yaml file
    tmuxp load ./myfile.yaml
    tmuxp load /abs/path/to/myfile.yaml
    tmuxp load ~/myfile.yaml

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

::

    tmuxp import tmuxinator /path/to/file.{json,yaml}

.. _import_tmuxinator:

From tmuxinator
~~~~~~~~~~~~~~~

::

    tmuxp import tmuxinator /path/to/file.{json,yaml}

.. _convert_config:

Convert between YAML and JSON
-----------------------------

::

    tmuxp convert /path/to/file.{json,yaml}

tmuxp automatically will prompt to convert ``.yaml`` to ``.json`` and
``.json`` to  ``.yaml``.
