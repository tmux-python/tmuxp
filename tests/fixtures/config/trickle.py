before = {  # shell_command_before is string in some areas
    "session_name": "sampleconfig",
    "start_directory": "/var",
    "windows": [
        {
            "window_name": "editor",
            "start_directory": "log",
            "panes": [
                {"shell_command": [{"cmd": "vim"}]},
                {"shell_command": [{"cmd": 'cowsay "hey"'}]},
            ],
            "layout": "main-verticle",
        },
        {
            "window_name": "logging",
            "start_directory": "~",
            "panes": [
                {"shell_command": [{"cmd": "tail -F /var/log/syslog"}]},
                {"shell_command": []},
            ],
        },
    ],
}

expected = {  # shell_command_before is string in some areas
    "session_name": "sampleconfig",
    "start_directory": "/var",
    "windows": [
        {
            "window_name": "editor",
            "start_directory": "/var/log",
            "panes": [
                {"shell_command": [{"cmd": "vim"}]},
                {"shell_command": [{"cmd": 'cowsay "hey"'}]},
            ],
            "layout": "main-verticle",
        },
        {
            "start_directory": "~",
            "window_name": "logging",
            "panes": [
                {"shell_command": [{"cmd": "tail -F /var/log/syslog"}]},
                {"shell_command": []},
            ],
        },
    ],
}
