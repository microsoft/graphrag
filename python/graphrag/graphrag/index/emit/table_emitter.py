#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""TableEmitter protocol for emitting tables to a destination."""
from typing import Protocol

import pandas as pd


class TableEmitter(Protocol):
    """TableEmitter protocol for emitting tables to a destination."""

    async def emit(self, name: str, data: pd.DataFrame) -> None:
        """Emit a dataframe to storage."""
