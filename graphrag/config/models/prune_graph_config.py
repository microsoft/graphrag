# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

import graphrag.config.defaults as defs


class PruneGraphConfig(BaseModel):
    """Configuration section for pruning graphs."""

    min_node_freq: int = Field(
        description="The minimum node frequency to allow.",
        default=defs.PRUNE_MIN_NODE_FREQ,
    )
    max_node_freq_std: float | None = Field(
        description="The maximum standard deviation of node frequency to allow.",
        default=defs.PRUNE_MAX_NODE_FREQ_STD,
    )
    min_node_degree: int = Field(
        description="The minimum node degree to allow.",
        default=defs.PRUNE_MIN_NODE_DEGREE,
    )
    max_node_degree_std: float | None = Field(
        description="The maximum standard deviation of node degree to allow.",
        default=defs.PRUNE_MAX_NODE_DEGREE_STD,
    )
    min_edge_weight_pct: float = Field(
        description="The minimum edge weight percentile to allow. Use e.g, `40` for 40%.",
        default=defs.PRUNE_MIN_EDGE_WEIGHT_PCT,
    )
    remove_ego_nodes: bool = Field(
        description="Remove ego nodes.", default=defs.PRUNE_REMOVE_EGO_NODES
    )
    lcc_only: bool = Field(
        description="Only use largest connected component.", default=defs.PRUNE_LCC_ONLY
    )
