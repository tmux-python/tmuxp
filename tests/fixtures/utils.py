import pathlib

from ..constants import FIXTURE_PATH


def get_config_file(_file):  # return fixture data, relative to __file__
    return FIXTURE_PATH / _file


def read_config_file(_file):  # return fixture data, relative to __file__
    return open(get_config_file(_file)).read()


def write_config(
    config_path: pathlib.Path, filename: str, content: str
) -> pathlib.Path:
    config = config_path / filename
    config.write_text(content, encoding="utf-8")
    return config
