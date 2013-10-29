.. _about:

=====
About
=====

tmuxp helps you manage your text-based workspaces. Its BSD licensed.

Internally, tmuxp is an object relational mapper on top of tmux.
End-users may use YAML, JSON and :py:obj:`dict` configurations to launch
workspaces like `tmuxinator`_ and `teamocil`_.

To jump right in, see :ref:`quickstart` and :ref:`examples`.

Interested in some kung-fu or joining the effort? :ref:`api` and
:ref:`developing`

License  is `BSD-licensed`_. Code can be found at github at
http://github.com/tony/tmuxp.

How is tmuxp different from teamocil and tmuxinator
---------------------------------------------------

teamocil and tmuxinator both build tmux workspaces from yaml. tmuxp
also handles building workspaces.

teamocil and tmuxinator do this by turning YAML directly into tmux
commands.

.. _attempt at 1.7 test: https://travis-ci.org/tony/tmuxp/jobs/12348263
.. _kaptan: https://github.com/emre/kaptan
.. _unittest: http://docs.python.org/2/library/unittest.html
.. _BSD-licensed: http://opensource.org/licenses/BSD-2-Clause
.. _tmuxinator: https://github.com/aziz/tmuxinator
.. _teamocil: https://github.com/remiprev/teamocil
