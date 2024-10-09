# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

import graphrag.config.defaults as defs


class ClusterGraphConfig(BaseModel):
    """Configuration section for clustering graphs."""

    max_cluster_size: int = Field(
        description="The maximum cluster size to use.", default=defs.MAX_CLUSTER_SIZE
    )
    strategy: dict | None = Field(
        description="The cluster strategy to use.", default=None
    )

    def resolved_strategy(self) -> dict:
        """Get the resolved cluster strategy."""
        from graphrag.index.operations.cluster_graph import GraphCommunityStrategyType

        return self.strategy or {
            "type": GraphCommunityStrategyType.leiden,
            "max_cluster_size": self.max_cluster_size,
        }
