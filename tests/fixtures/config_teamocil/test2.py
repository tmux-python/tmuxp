from .. import utils as test_utils

teamocil_yaml = test_utils.read_config_file("config_teamocil/test2.yaml")
teamocil_dict = {
    "windows": [
        {
            "name": "sample-four-panes",
            "root": "~/Code/sample/www",
            "layout": "tiled",
            "panes": [{"cmd": "pwd"}, {"cmd": "pwd"}, {"cmd": "pwd"}, {"cmd": "pwd"}],
        }
    ]
}

expected = {
    "session_name": None,
    "windows": [
        {
            "window_name": "sample-four-panes",
            "layout": "tiled",
            "start_directory": "~/Code/sample/www",
            "panes": [
                {"shell_command": "pwd"},
                {"shell_command": "pwd"},
                {"shell_command": "pwd"},
                {"shell_command": "pwd"},
            ],
        }
    ],
}
