# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from __future__ import annotations

import typing

import pandas as pd

Context_T: typing.TypeAlias = typing.Tuple[typing.Union[str, typing.List[str]], typing.Dict[str, pd.DataFrame]]

SingleContext_T: typing.TypeAlias = typing.Tuple[str, typing.Dict[str, pd.DataFrame]]
