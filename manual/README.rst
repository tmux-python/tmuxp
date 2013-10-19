For studying the differences between prior tmux versions to check
compatibility with legacy versions.

Get source:

.. code-block:: bash

    $ git clone git://git.code.sf.net/p/tmux/tmux-code tmux-tmux-code tmux
    $ cd tmux

Converted with:

.. code-block:: bash

    $ git checkout <version>
    $ ./configure
    $ make
    $ groff -t -e -mandoc -Tascii tmux.1 | col -bx > manpage.txt

repeat for versions.

Create a git-diff style diff of version manuals:

.. code-block:: bash

    $ diff -u 1.6 1.8 > 1_6__1_8.diff
