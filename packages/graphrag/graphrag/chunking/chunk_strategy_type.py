# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Chunk strategy type enumeration."""

from enum import Enum


class ChunkStrategyType(str, Enum):
    """ChunkStrategy class definition."""

    tokens = "tokens"
    sentence = "sentence"

    def __repr__(self):
        """Get a string representation."""
        return f'"{self.value}"'
