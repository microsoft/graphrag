#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""A module containing 'BasicMergeOperation', 'StringOperation', 'NumericOperation' and 'DetailedAttributeMergeOperation' models."""
from dataclasses import dataclass
from enum import Enum


class BasicMergeOperation(str, Enum):
    """Basic Merge Operation class definition."""

    Replace = "replace"
    Skip = "skip"


class StringOperation(str, Enum):
    """String Operation class definition."""

    Concat = "concat"
    Replace = "replace"
    Skip = "skip"


class NumericOperation(str, Enum):
    """Numeric Operation class definition."""

    Sum = "sum"
    Average = "average"
    Max = "max"
    Min = "min"
    Multiply = "multiply"
    Replace = "replace"
    Skip = "skip"


@dataclass
class DetailedAttributeMergeOperation:
    """Detailed attribute merge operation class definition."""

    operation: str  # StringOperation | NumericOperation

    # concat
    separator: str | None = None
    delimiter: str | None = None
    distinct: bool = False


AttributeMergeOperation = str | DetailedAttributeMergeOperation
