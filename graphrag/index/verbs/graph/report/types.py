# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""A module containing the community reports strategy enum."""

from enum import Enum


class CreateCommunityReportsStrategyType(str, Enum):
    """CreateCommunityReportsStrategyType class definition."""

    graph_intelligence = "graph_intelligence"

    def __repr__(self):
        """Get a string representation."""
        return f'"{self.value}"'
