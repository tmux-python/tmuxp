import os

before_config = {
    "session_name": "sampleconfig",
    "start_directory": "~",
    "windows": [
        {
            "window_name": "editor",
            "panes": [
                {"shell_command": ["vim", "top"]},
                {"shell_command": ["vim"]},
                {"shell_command": 'cowsay "hey"'},
            ],
            "layout": "main-verticle",
        },
        {
            "window_name": "logging",
            "panes": [{"shell_command": ["tail -F /var/log/syslog"]}],
        },
        {
            "start_directory": "/var/log",
            "options": {"automatic-rename": True},
            "panes": [{"shell_command": "htop"}, "vim"],
        },
        {"start_directory": "./", "panes": ["pwd"]},
        {"start_directory": "./asdf/", "panes": ["pwd"]},
        {"start_directory": "../", "panes": ["pwd"]},
        {"panes": ["top"]},
    ],
}


def after_config():
    return {
        "session_name": "sampleconfig",
        "start_directory": os.path.expanduser("~"),
        "windows": [
            {
                "window_name": "editor",
                "panes": [
                    {"shell_command": [{"cmd": "vim"}, {"cmd": "top"}]},
                    {"shell_command": [{"cmd": "vim"}]},
                    {"shell_command": [{"cmd": 'cowsay "hey"'}]},
                ],
                "layout": "main-verticle",
            },
            {
                "window_name": "logging",
                "panes": [{"shell_command": [{"cmd": "tail -F /var/log/syslog"}]}],
            },
            {
                "start_directory": "/var/log",
                "options": {"automatic-rename": True},
                "panes": [
                    {"shell_command": [{"cmd": "htop"}]},
                    {"shell_command": [{"cmd": "vim"}]},
                ],
            },
            {
                "start_directory": os.path.normpath(
                    os.path.join(os.path.expanduser("~"), "./")
                ),
                "panes": [{"shell_command": [{"cmd": "pwd"}]}],
            },
            {
                "start_directory": os.path.normpath(
                    os.path.join(os.path.expanduser("~"), "./asdf")
                ),
                "panes": [{"shell_command": [{"cmd": "pwd"}]}],
            },
            {
                "start_directory": os.path.normpath(
                    os.path.join(os.path.expanduser("~"), "../")
                ),
                "panes": [{"shell_command": [{"cmd": "pwd"}]}],
            },
            {"panes": [{"shell_command": [{"cmd": "top"}]}]},
        ],
    }
