#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""Table Emitter Types."""
from enum import Enum


class TableEmitterType(str, Enum):
    """Table Emitter Types."""

    Json = "json"
    Parquet = "parquet"
    CSV = "csv"
