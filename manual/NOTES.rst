===================
Compatibility notes
===================

master
------

src: http://sourceforge.net/p/tmux/tmux-code/ci/master/tree/

1.8
---

src: http://sourceforge.net/p/tmux/tmux-code/ci/1.8/tree/

1.7
---

src: http://sourceforge.net/p/tmux/tmux-code/ci/1.7/tree/

1.6
---

src: http://sourceforge.net/p/tmux/tmux-code/ci/1.6/tree/

new-window
""""""""""

src: http://sourceforge.net/p/tmux/tmux-code/ci/1.6/tree/cmd-new-window.c

.. code-block:: c

	if (args_has(args, 'P'))
		ctx->print(ctx, "%s:%u", s->name, wl->idx);
	return (0);

split-window
""""""""""""

src: http://sourceforge.net/p/tmux/tmux-code/ci/1.6/tree/cmd-split-window.c

.. code-block:: c

	if (args_has(args, 'P')) {
		if (window_pane_index(new_wp, &paneidx) != 0)
			fatalx("index not found");
		ctx->print(ctx, "%s:%u.%u", s->name, wl->idx, paneidx);
	}
	return (0);

list-sessions
"""""""""""""

src: http://sourceforge.net/p/tmux/tmux-code/ci/1.6/tree/cmd-list-sessions.c

.. code-block:: c

    template = "#{session_name}: #{session_windows} windows "
        "(created #{session_created_string}) [#{session_width}x"
        "#{session_height}]#{?session_grouped, (group ,}"
        "#{session_group}#{?session_grouped,),}"
        "#{?session_attached, (attached),}";

list-windows
""""""""""""

src: http://sourceforge.net/p/tmux/tmux-code/ci/1.6/tree/cmd-list-windows.c

.. code-block:: c

    template = "#{session_name}:#{window_index}: "
        "#{window_name} "
        "[#{window_width}x#{window_height}] "
        "[layout #{window_layout}]"
        "#{?window_active, (active),}";


list-panes
""""""""""

src: http://sourceforge.net/p/tmux/tmux-code/ci/1.6/tree/cmd-list-panes.c

.. code-block:: c

    template = "#{session_name}:#{window_index}.#{pane_index}: "
        "[#{pane_width}x#{pane_height}] [history "
        "#{history_size}/#{history_limit}, "
        "#{history_bytes} bytes] #{pane_id}"
        "#{?pane_active, (active),}#{?pane_dead, (dead),}";
