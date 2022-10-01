import json
import pathlib
import typing as t

import yaml

if t.TYPE_CHECKING:
    from typing_extensions import Literal, TypeAlias

    FormatLiteral = Literal["json", "yaml"]

    RawConfigData: TypeAlias = t.Dict[t.Any, t.Any]


class ConfigReader:
    r"""Parse string data (YAML and JSON) into a dictionary.

    >>> cfg = ConfigReader({ "session_name": "my session" })
    >>> cfg.dump("yaml")
    'session_name: my session\n'
    >>> cfg.dump("json")
    '{\n  "session_name": "my session"\n}'
    """

    def __init__(self, content: "RawConfigData"):
        self.content = content

    @staticmethod
    def _load(format: "FormatLiteral", content: str):
        """Load raw config data and directly return it.

        >>> ConfigReader._load("json", '{ "session_name": "my session" }')
        {'session_name': 'my session'}

        >>> ConfigReader._load("yaml", 'session_name: my session')
        {'session_name': 'my session'}
        """
        if format == "yaml":
            return yaml.load(
                content,
                Loader=yaml.SafeLoader,
            )
        elif format == "json":
            return json.loads(content)
        else:
            raise NotImplementedError(f"{format} not supported in configuration")

    @classmethod
    def load(cls, format: "FormatLiteral", content: str):
        """Load raw config data into a ConfigReader instance (to dump later).

        >>> cfg = ConfigReader.load("json", '{ "session_name": "my session" }')
        >>> cfg
        <tmuxp.config_reader.ConfigReader object at ...>
        >>> cfg.content
        {'session_name': 'my session'}

        >>> cfg = ConfigReader.load("yaml", 'session_name: my session')
        >>> cfg
        <tmuxp.config_reader.ConfigReader object at ...>
        >>> cfg.content
        {'session_name': 'my session'}
        """
        return cls(
            content=cls._load(
                format=format,
                content=content,
            ),
        )

    @classmethod
    def _from_file(cls, path: pathlib.Path):
        r"""Load data from file path directly to dictionary.

        **YAML file**

        *For demonstration only,* create a YAML file:

        >>> yaml_file = tmp_path / 'my_config.yaml'
        >>> yaml_file.write_text('session_name: my session', encoding='utf-8')
        24

        *Read YAML file*:

        >>> ConfigReader._from_file(yaml_file)
        {'session_name': 'my session'}

        **JSON file**

        *For demonstration only,* create a JSON file:

        >>> json_file = tmp_path / 'my_config.json'
        >>> json_file.write_text('{"session_name": "my session"}', encoding='utf-8')
        30

        *Read JSON file*:

        >>> ConfigReader._from_file(json_file)
        {'session_name': 'my session'}
        """
        assert isinstance(path, pathlib.Path)
        content = open(path).read()

        if path.suffix in [".yaml", ".yml"]:
            format: FormatLiteral = "yaml"
        elif path.suffix == ".json":
            format = "json"
        else:
            raise NotImplementedError(f"{path.suffix} not supported in {path}")

        return cls._load(
            format=format,
            content=content,
        )

    @classmethod
    def from_file(cls, path: pathlib.Path):
        r"""Load data from file path

        **YAML file**

        *For demonstration only,* create a YAML file:

        >>> yaml_file = tmp_path / 'my_config.yaml'
        >>> yaml_file.write_text('session_name: my session', encoding='utf-8')
        24

        *Read YAML file*:

        >>> cfg = ConfigReader.from_file(yaml_file)
        >>> cfg
        <tmuxp.config_reader.ConfigReader object at ...>

        >>> cfg.content
        {'session_name': 'my session'}

        **JSON file**

        *For demonstration only,* create a JSON file:

        >>> json_file = tmp_path / 'my_config.json'
        >>> json_file.write_text('{"session_name": "my session"}', encoding='utf-8')
        30

        *Read JSON file*:

        >>> cfg = ConfigReader.from_file(json_file)
        >>> cfg
        <tmuxp.config_reader.ConfigReader object at ...>

        >>> cfg.content
        {'session_name': 'my session'}
        """
        return cls(content=cls._from_file(path=path))

    @staticmethod
    def _dump(
        format: "FormatLiteral",
        content: "RawConfigData",
        indent: int = 2,
        **kwargs: t.Any,
    ) -> str:
        r"""Dump directly.

        >>> ConfigReader._dump("yaml", { "session_name": "my session" })
        'session_name: my session\n'

        >>> ConfigReader._dump("json", { "session_name": "my session" })
        '{\n  "session_name": "my session"\n}'
        """
        if format == "yaml":
            return yaml.dump(
                content,
                indent=2,
                default_flow_style=False,
                Dumper=yaml.SafeDumper,
            )
        elif format == "json":
            return json.dumps(
                content,
                indent=2,
            )
        else:
            raise NotImplementedError(f"{format} not supported in config")

    def dump(self, format: "FormatLiteral", indent: int = 2, **kwargs: t.Any) -> str:
        r"""Dump via ConfigReader instance.

        >>> cfg = ConfigReader({ "session_name": "my session" })
        >>> cfg.dump("yaml")
        'session_name: my session\n'
        >>> cfg.dump("json")
        '{\n  "session_name": "my session"\n}'
        """
        return self._dump(
            format=format,
            content=self.content,
            indent=indent,
            **kwargs,
        )
