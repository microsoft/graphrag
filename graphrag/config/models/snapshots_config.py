# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

import graphrag.config.defaults as defs


class SnapshotsConfig(BaseModel):
    """Configuration section for snapshots."""

    graphml: bool = Field(
        description="A flag indicating whether to take snapshots of GraphML.",
        default=defs.SNAPSHOTS_GRAPHML,
    )
    raw_entities: bool = Field(
        description="A flag indicating whether to take snapshots of raw entities.",
        default=defs.SNAPSHOTS_RAW_ENTITIES,
    )
    top_level_nodes: bool = Field(
        description="A flag indicating whether to take snapshots of top-level nodes.",
        default=defs.SNAPSHOTS_TOP_LEVEL_NODES,
    )
