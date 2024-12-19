# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing different lists and dictionaries."""

# Use this for now instead of a wrapper
from enum import Enum
from typing import Any


class EmbedGraphStrategyType(str, Enum):
    """EmbedGraphStrategyType class definition."""

    node2vec = "node2vec"

    def __repr__(self):
        """Get a string representation."""
        return f'"{self.value}"'


NodeList = list[str]
EmbeddingList = list[Any]
NodeEmbeddings = dict[str, list[float]]
"""Label -> Embedding"""
