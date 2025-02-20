# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

from graphrag.config.defaults import graphrag_config_defaults


class ClusterGraphConfig(BaseModel):
    """Configuration section for clustering graphs."""

    max_cluster_size: int = Field(
        description="The maximum cluster size to use.",
        default=graphrag_config_defaults.cluster_graph.max_cluster_size,
    )
    use_lcc: bool = Field(
        description="Whether to use the largest connected component.",
        default=graphrag_config_defaults.cluster_graph.use_lcc,
    )
    seed: int = Field(
        description="The seed to use for the clustering.",
        default=graphrag_config_defaults.cluster_graph.seed,
    )
