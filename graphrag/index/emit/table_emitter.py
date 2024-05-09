# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""TableEmitter protocol for emitting tables to a destination."""

from typing import Protocol

import pandas as pd


class TableEmitter(Protocol):
    """TableEmitter protocol for emitting tables to a destination."""

    async def emit(self, name: str, data: pd.DataFrame) -> None:
        """Emit a dataframe to storage."""
