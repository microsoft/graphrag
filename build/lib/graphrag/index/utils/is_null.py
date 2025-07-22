# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Defines the is_null utility."""

import math
from typing import Any


def is_null(value: Any) -> bool:
    """Check if value is null or is nan."""

    def is_none() -> bool:
        return value is None

    def is_nan() -> bool:
        return isinstance(value, float) and math.isnan(value)

    return is_none() or is_nan()
