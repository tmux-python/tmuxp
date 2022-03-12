import pathlib

FIXTURE_PATH = pathlib.Path(__file__).parent


def load_fixture(_file):  # return fixture data, relative to __file__
    return open(FIXTURE_PATH / _file).read()


def write_config(
    config_path: pathlib.Path, filename: str, content: str
) -> pathlib.Path:
    config = config_path / filename
    config.write_text(content, encoding="utf-8")
    return config
