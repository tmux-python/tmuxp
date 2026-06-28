"""Objects that are not valid workspace builders, used by resolution tests."""

from __future__ import annotations

import typing as t


class NotABuilder:
    """A class missing the required ``build`` method."""


class MissingPluginsBuilder:
    """A builder whose constructor omits the ``plugins`` parameter."""

    def __init__(self, session_config: t.Any, server: t.Any) -> None:
        self.session_config = session_config

    def build(self, session: t.Any = None, append: bool = False) -> None:
        """No-op build for validation tests."""
