"""Internal :term:`type annotations <annotation>`.

Notes
-----
:class:`StrPath` and :class:`StrOrBytesPath` is based on `typeshed's`_.

.. _typeshed's: https://github.com/python/typeshed/blob/9687d5/stdlib/_typeshed/__init__.pyi#L98
"""  # E501
from os import PathLike
from typing import Union

StrPath = Union[str, "PathLike[str]"]
""":class:`os.PathLike` or :class:`str`"""
