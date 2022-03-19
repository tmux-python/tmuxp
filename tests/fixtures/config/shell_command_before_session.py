from .._util import read_config_file

before = read_config_file("config/shell_command_before_session.yaml")
expected = read_config_file("config/shell_command_before_session-expected.yaml")
