"""Privacy-aware path utilities for hiding sensitive directory information.

This module provides utilities for masking user home directories in path output,
useful for logging, debugging, and displaying paths without exposing PII.
"""

from __future__ import annotations

import os
import pathlib
import typing as t

if t.TYPE_CHECKING:
    PrivatePathBase = pathlib.Path
else:
    PrivatePathBase = type(pathlib.Path())


class PrivatePath(PrivatePathBase):
    """Path subclass that hides the user's home directory in textual output.

    The class behaves like :class:`pathlib.Path`, but normalizes string and
    representation output to replace the current user's home directory with
    ``~``. This is useful when logging or displaying paths that should not leak
    potentially sensitive information.

    Examples
    --------
    >>> from pathlib import Path
    >>> home = Path.home()

    >>> PrivatePath(home)
    PrivatePath('~')

    >>> PrivatePath(home / "projects" / "tmuxp")
    PrivatePath('~/projects/tmuxp')

    >>> str(PrivatePath("/tmp/example"))
    '/tmp/example'

    >>> f'config: {PrivatePath(home / ".tmuxp" / "config.yaml")}'  # doctest: +ELLIPSIS
    'config: ~/.tmuxp/config.yaml'
    """

    def __new__(cls, *args: t.Any, **kwargs: t.Any) -> PrivatePath:
        """Create a new PrivatePath instance."""
        return super().__new__(cls, *args, **kwargs)

    @classmethod
    def _collapse_home(cls, value: str) -> str:
        """Collapse the user's home directory to ``~`` in ``value``.

        Parameters
        ----------
        value : str
            Path string to process

        Returns
        -------
        str
            Path with home directory replaced by ``~`` if applicable

        Examples
        --------
        >>> import pathlib
        >>> home = str(pathlib.Path.home())
        >>> PrivatePath._collapse_home(home)
        '~'
        >>> PrivatePath._collapse_home(home + "/projects")
        '~/projects'
        >>> PrivatePath._collapse_home("/tmp/test")
        '/tmp/test'
        >>> PrivatePath._collapse_home("~/already/collapsed")
        '~/already/collapsed'
        """
        if value.startswith("~"):
            return value

        home = str(pathlib.Path.home())
        if value == home:
            return "~"

        separators = {os.sep}
        if os.altsep:
            separators.add(os.altsep)

        for sep in separators:
            home_with_sep = home + sep
            if value.startswith(home_with_sep):
                return "~" + value[len(home) :]

        return value

    def __str__(self) -> str:
        """Return string representation with home directory collapsed to ~."""
        original = pathlib.Path.__str__(self)
        return self._collapse_home(original)

    def __repr__(self) -> str:
        """Return repr with home directory collapsed to ~."""
        return f"{self.__class__.__name__}({str(self)!r})"


def collapse_home_in_string(text: str) -> str:
    """Collapse home directory paths within a colon-separated string.

    Useful for processing PATH-like environment variables that may contain
    multiple paths, some of which are under the user's home directory.

    Parameters
    ----------
    text : str
        String potentially containing paths separated by colons (or semicolons
        on Windows)

    Returns
    -------
    str
        String with home directory paths collapsed to ``~``

    Examples
    --------
    >>> import pathlib
    >>> home = str(pathlib.Path.home())
    >>> collapse_home_in_string(f"{home}/.local/bin:/usr/bin")  # doctest: +ELLIPSIS
    '~/.local/bin:/usr/bin'
    >>> collapse_home_in_string("/usr/bin:/bin")
    '/usr/bin:/bin'
    >>> path_str = f"{home}/bin:{home}/.cargo/bin:/usr/bin"
    >>> collapse_home_in_string(path_str)  # doctest: +ELLIPSIS
    '~/bin:~/.cargo/bin:/usr/bin'
    """
    # Handle both Unix (:) and Windows (;) path separators
    separator = ";" if os.name == "nt" else ":"
    parts = text.split(separator)
    collapsed = [PrivatePath._collapse_home(part) for part in parts]
    return separator.join(collapsed)


__all__ = ["PrivatePath", "collapse_home_in_string"]
