from .._util import read_config_file

teamocil_yaml = read_config_file("config_teamocil/test4.yaml")

teamocil_dict = {
    "windows": [
        {
            "name": "erb-example",
            "root": "<%= ENV['MY_PROJECT_ROOT'] %>",
            "panes": [{"cmd": "pwd"}],
        }
    ]
}

expected = {
    "session_name": None,
    "windows": [
        {
            "window_name": "erb-example",
            "start_directory": "<%= ENV['MY_PROJECT_ROOT'] %>",
            "panes": [{"shell_command": "pwd"}],
        }
    ],
}
