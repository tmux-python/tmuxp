import dataclasses
import typing as t


@dataclasses.dataclass
class ConfigTestData:
    expand1: t.Any
    expand2: t.Any
    expand_blank: t.Any
    sampleconfig: t.Any
    shell_command_before: t.Any
    shell_command_before_session: t.Any
    trickle: t.Any
