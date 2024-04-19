# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

from graphrag.config.defaults import (
    DEFAULT_MAX_CLUSTER_SIZE,
)
from graphrag.index.verbs.graph.clustering import GraphCommunityStrategyType


class ClusterGraphConfigModel(BaseModel):
    """Configuration section for clustering graphs."""

    max_cluster_size: int = Field(
        description="The maximum cluster size to use.", default=DEFAULT_MAX_CLUSTER_SIZE
    )
    strategy: dict | None = Field(
        description="The cluster strategy to use.", default=None
    )

    def resolved_strategy(self) -> dict:
        """Get the resolved cluster strategy."""
        return self.strategy or {
            "type": GraphCommunityStrategyType.leiden,
            "max_cluster_size": self.max_cluster_size,
        }
