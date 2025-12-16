# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License


"""Builtin cache implementation types."""

from enum import StrEnum


class CacheType(StrEnum):
    """Enum for cache types."""

    Json = "json"
    Memory = "memory"
    Noop = "none"
