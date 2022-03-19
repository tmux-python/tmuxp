from .. import utils as test_utils

before = test_utils.read_config_file("config/shell_command_before_session.yaml")
expected = test_utils.read_config_file(
    "config/shell_command_before_session-expected.yaml"
)
