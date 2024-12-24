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
    use_lcc: bool = Field(
        description="Whether to use the largest connected component.",
        default=defs.USE_LCC,
    )
    seed: int | None = Field(
        description="The seed to use for the clustering.",
        default=defs.CLUSTER_GRAPH_SEED,
    )
