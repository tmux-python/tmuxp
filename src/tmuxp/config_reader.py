import json
import pathlib
import typing as t

import yaml

if t.TYPE_CHECKING:
    from typing_extensions import Literal, TypeAlias

    FormatLiteral = Literal["json", "yaml"]

    RawConfigData: TypeAlias = t.Dict[t.Any, t.Any]


class ConfigReader:
    """Reads raw config data"""

    def __init__(
        self,
        content: "RawConfigData",
    ):
        self.content = content

    @staticmethod
    def _load(format: "FormatLiteral", content: str):
        """Load raw config data."""
        if format == "yaml":
            return yaml.load(content, Loader=yaml.SafeLoader)
        elif format == "json":
            return json.loads(content)
        else:
            raise NotImplementedError(f"{format} not supported in configuration")

    @classmethod
    def load(cls, format: "FormatLiteral", content: str):
        """Load raw config data."""
        return cls(content=cls._load(format=format, content=content))

    @classmethod
    def _from_file(cls, path: pathlib.Path):
        """Load data from file path"""
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
        return cls(content=cls._from_file(path=path))

    @staticmethod
    def _dump(
        format: "FormatLiteral",
        content: "RawConfigData",
        indent: int = 2,
        **kwargs: t.Any,
    ) -> str:
        if format == "yaml":
            return yaml.dump(
                content, indent=2, default_flow_style=False, Dumper=yaml.SafeDumper
            )
        elif format == "json":
            return json.dumps(content, indent=2)
        else:
            raise NotImplementedError(f"{format} not supported in config")

    def dump(self, format: "FormatLiteral", indent: int = 2, **kwargs: t.Any) -> str:
        return self._dump(format=format, content=self.content, indent=indent, **kwargs)
