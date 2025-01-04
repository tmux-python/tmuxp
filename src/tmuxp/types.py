"""Internal :term:`type annotations <annotation>`.

Notes
-----
:class:`StrPath` and :class:`StrOrBytesPath` is based on `typeshed's`_.

.. _typeshed's: https://github.com/python/typeshed/blob/9687d5/stdlib/_typeshed/__init__.pyi#L98
"""  # E501

from __future__ import annotations

import typing as t

if t.TYPE_CHECKING:
    from os import PathLike

StrPath = t.Union[str, "PathLike[str]"]
""":class:`os.PathLike` or :class:`str`"""
