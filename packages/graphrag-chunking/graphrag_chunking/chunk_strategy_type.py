# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Chunk strategy type enumeration."""

from enum import StrEnum


class ChunkerType(StrEnum):
    """ChunkerType class definition."""

    Tokens = "tokens"
    Sentence = "sentence"
