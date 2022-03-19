from .. import utils as test_utils

tmuxinator_yaml = test_utils.read_config_file("config_tmuxinator/test3.yaml")

tmuxinator_dict = {
    "name": "sample",
    "root": "~/test",
    "socket_name": "foo",
    "tmux_options": "-f ~/.tmux.mac.conf",
    "pre": "sudo /etc/rc.d/mysqld start",
    "pre_window": "rbenv shell 2.0.0-p247",
    "windows": [
        {
            "editor": {
                "pre": [
                    'echo "I get run in each pane, ' 'before each pane command!"',
                    None,
                ],
                "layout": "main-vertical",
                "root": "~/test/editor",
                "panes": ["vim", None, "top"],
            }
        },
        {"shell": ["git pull", "git merge"]},
        {
            "guard": {
                "layout": "tiled",
                "pre": [
                    'echo "I get run in each pane."',
                    'echo "Before each pane command!"',
                ],
                "panes": [None, None, None],
            }
        },
        {"database": "bundle exec rails db"},
        {"server": "bundle exec rails s"},
        {"logs": "tail -f log/development.log"},
        {"console": "bundle exec rails c"},
        {"capistrano": None},
        {"server": "ssh user@example.com"},
    ],
}

expected = {
    "session_name": "sample",
    "socket_name": "foo",
    "start_directory": "~/test",
    "config": "~/.tmux.mac.conf",
    "shell_command": "sudo /etc/rc.d/mysqld start",
    "shell_command_before": ["rbenv shell 2.0.0-p247"],
    "windows": [
        {
            "window_name": "editor",
            "shell_command_before": [
                'echo "I get run in each pane, before each pane command!"',
                None,
            ],
            "layout": "main-vertical",
            "start_directory": "~/test/editor",
            "panes": ["vim", None, "top"],
        },
        {"window_name": "shell", "panes": ["git pull", "git merge"]},
        {
            "window_name": "guard",
            "layout": "tiled",
            "shell_command_before": [
                'echo "I get run in each pane."',
                'echo "Before each pane command!"',
            ],
            "panes": [None, None, None],
        },
        {"window_name": "database", "panes": ["bundle exec rails db"]},
        {"window_name": "server", "panes": ["bundle exec rails s"]},
        {"window_name": "logs", "panes": ["tail -f log/development.log"]},
        {"window_name": "console", "panes": ["bundle exec rails c"]},
        {"window_name": "capistrano", "panes": [None]},
        {"window_name": "server", "panes": ["ssh user@example.com"]},
    ],
}
