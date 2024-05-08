# Copyright (c) 2024 Microsoft Corporation.

"""Table Emitter Types."""

from enum import Enum


class TableEmitterType(str, Enum):
    """Table Emitter Types."""

    Json = "json"
    Parquet = "parquet"
    CSV = "csv"
