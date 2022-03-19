from .. import utils as test_utils

tmuxinator_yaml = test_utils.read_config_file("config_tmuxinator/test2.yaml")

tmuxinator_dict = {
    "project_name": "sample",
    "project_root": "~/test",
    "socket_name": "foo",
    "pre": "sudo /etc/rc.d/mysqld start",
    "rbenv": "2.0.0-p247",
    "cli_args": "-f ~/.tmux.mac.conf",
    "tabs": [
        {
            "editor": {
                "pre": [
                    'echo "I get run in each pane, ' 'before each pane command!"',
                    None,
                ],
                "layout": "main-vertical",
                "panes": ["vim", None, "top"],
            }
        },
        {"shell": "git pull"},
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
    "config": "~/.tmux.mac.conf",
    "start_directory": "~/test",
    "shell_command_before": ["sudo /etc/rc.d/mysqld start", "rbenv shell 2.0.0-p247"],
    "windows": [
        {
            "window_name": "editor",
            "shell_command_before": [
                'echo "I get run in each pane, before each pane command!"',
                None,
            ],
            "layout": "main-vertical",
            "panes": ["vim", None, "top"],
        },
        {"window_name": "shell", "panes": ["git pull"]},
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
