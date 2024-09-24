# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Table Emitter Types."""

from enum import Enum


class TableEmitterType(str, Enum):
    """Table Emitter Types."""

    Json = "json"
    Parquet = "parquet"
    CSV = "csv"

    def __str__(self):
        """Return the string representation of the enum value."""
        return self.value
