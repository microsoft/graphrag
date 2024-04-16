# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

from graphrag.index.default_config.parameters.defaults import (
    DEFAULT_SNAPSHOTS_GRAPHML,
    DEFAULT_SNAPSHOTS_RAW_ENTITIES,
    DEFAULT_SNAPSHOTS_TOP_LEVEL_NODES,
)


class SnapshotsConfigModel(BaseModel):
    """Configuration section for snapshots."""

    graphml: bool | None = Field(
        description="A flag indicating whether to take snapshots of GraphML.",
        default=DEFAULT_SNAPSHOTS_GRAPHML,
    )
    raw_entities: bool | None = Field(
        description="A flag indicating whether to take snapshots of raw entities.",
        default=DEFAULT_SNAPSHOTS_RAW_ENTITIES,
    )
    top_level_nodes: bool | None = Field(
        description="A flag indicating whether to take snapshots of top-level nodes.",
        default=DEFAULT_SNAPSHOTS_TOP_LEVEL_NODES,
    )
