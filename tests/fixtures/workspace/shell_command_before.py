"""Test fixture for tmuxp to demonstrate shell_command_before."""

import pathlib
import typing as t

config_unexpanded = {  # shell_command_before is string in some areas
    "session_name": "sample workspace",
    "start_directory": "/",
    "windows": [
        {
            "window_name": "editor",
            "start_directory": "~",
            "shell_command_before": "source .venv/bin/activate",
            "panes": [
                {"shell_command": ["vim"]},
                {
                    "shell_command_before": ["rbenv local 2.0.0-p0"],
                    "shell_command": ['cowsay "hey"'],
                },
            ],
            "layout": "main-vertical",
        },
        {
            "shell_command_before": "rbenv local 2.0.0-p0",
            "window_name": "logging",
            "panes": [{"shell_command": ["tail -F /var/log/syslog"]}, {}],
        },
        {
            "window_name": "shufu",
            "panes": [
                {
                    "shell_command_before": ["rbenv local 2.0.0-p0"],
                    "shell_command": ["htop"],
                },
            ],
        },
        {"options": {"automatic-rename": True}, "panes": [{"shell_command": ["htop"]}]},
        {"panes": ["top"]},
    ],
}


def config_expanded() -> t.Dict[str, t.Any]:
    """Return expanded configuration for shell_command_before example."""
    return {  # shell_command_before is string in some areas
        "session_name": "sample workspace",
        "start_directory": "/",
        "windows": [
            {
                "window_name": "editor",
                "start_directory": str(pathlib.Path().home()),
                "shell_command_before": {
                    "shell_command": [{"cmd": "source .venv/bin/activate"}],
                },
                "panes": [
                    {"shell_command": [{"cmd": "vim"}]},
                    {
                        "shell_command_before": {
                            "shell_command": [{"cmd": "rbenv local 2.0.0-p0"}],
                        },
                        "shell_command": [{"cmd": 'cowsay "hey"'}],
                    },
                ],
                "layout": "main-vertical",
            },
            {
                "shell_command_before": {
                    "shell_command": [{"cmd": "rbenv local 2.0.0-p0"}],
                },
                "window_name": "logging",
                "panes": [
                    {"shell_command": [{"cmd": "tail -F /var/log/syslog"}]},
                    {"shell_command": []},
                ],
            },
            {
                "window_name": "shufu",
                "panes": [
                    {
                        "shell_command_before": {
                            "shell_command": [{"cmd": "rbenv local 2.0.0-p0"}],
                        },
                        "shell_command": [{"cmd": "htop"}],
                    },
                ],
            },
            {
                "options": {"automatic-rename": True},
                "panes": [{"shell_command": [{"cmd": "htop"}]}],
            },
            {"panes": [{"shell_command": [{"cmd": "top"}]}]},
        ],
    }


def config_after() -> t.Dict[str, t.Any]:
    """Return expected configuration for shell_command_before example."""
    return {  # shell_command_before is string in some areas
        "session_name": "sample workspace",
        "start_directory": "/",
        "windows": [
            {
                "window_name": "editor",
                "start_directory": str(pathlib.Path().home()),
                "shell_command_before": {
                    "shell_command": [{"cmd": "source .venv/bin/activate"}],
                },
                "panes": [
                    {
                        "shell_command": [
                            {"cmd": "source .venv/bin/activate"},
                            {"cmd": "vim"},
                        ],
                    },
                    {
                        "shell_command_before": {
                            "shell_command": [{"cmd": "rbenv local 2.0.0-p0"}],
                        },
                        "shell_command": [
                            {"cmd": "source .venv/bin/activate"},
                            {"cmd": "rbenv local 2.0.0-p0"},
                            {"cmd": 'cowsay "hey"'},
                        ],
                    },
                ],
                "layout": "main-vertical",
            },
            {
                "shell_command_before": {
                    "shell_command": [{"cmd": "rbenv local 2.0.0-p0"}],
                },
                "start_directory": "/",
                "window_name": "logging",
                "panes": [
                    {
                        "shell_command": [
                            {"cmd": "rbenv local 2.0.0-p0"},
                            {"cmd": "tail -F /var/log/syslog"},
                        ],
                    },
                    {"shell_command": [{"cmd": "rbenv local 2.0.0-p0"}]},
                ],
            },
            {
                "start_directory": "/",
                "window_name": "shufu",
                "panes": [
                    {
                        "shell_command_before": {
                            "shell_command": [{"cmd": "rbenv local 2.0.0-p0"}],
                        },
                        "shell_command": [
                            {"cmd": "rbenv local 2.0.0-p0"},
                            {"cmd": "htop"},
                        ],
                    },
                ],
            },
            {
                "start_directory": "/",
                "options": {"automatic-rename": True},
                "panes": [{"shell_command": [{"cmd": "htop"}]}],
            },
            {"start_directory": "/", "panes": [{"shell_command": [{"cmd": "top"}]}]},
        ],
    }
