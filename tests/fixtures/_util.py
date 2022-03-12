import os
import pathlib


def curjoin(_file):  # return filepath relative to __file__ (this file)
    return os.path.join(os.path.dirname(__file__), _file)


def loadfixture(_file):  # return fixture data, relative to __file__
    return open(curjoin(_file)).read()


def write_config(
    config_path: pathlib.Path, filename: str, content: str
) -> pathlib.Path:
    config = config_path / filename
    config.write_text(content, encoding="utf-8")
    return config
