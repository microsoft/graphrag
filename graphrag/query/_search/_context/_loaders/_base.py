# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from __future__ import annotations

import abc
import os
import pathlib
import typing

from .. import _builders


class BaseContextLoader(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def from_parquet_directory(
        cls,
        directory: typing.Union[str, os.PathLike[str], pathlib.Path],
        **kwargs: str
    ) -> typing.Self: ...

    @abc.abstractmethod
    def to_context_builder(self, *args, **kwargs: typing.Any) -> _builders.BaseContextBuilder: ...
