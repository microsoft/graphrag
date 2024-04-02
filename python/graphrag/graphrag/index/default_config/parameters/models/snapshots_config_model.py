# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field


class SnapshotsConfigModel(BaseModel):
    """Configuration section for snapshots."""

    graphml: bool | None = Field(
        description="A flag indicating whether to take snapshots of GraphML.",
        default=None,
    )
    raw_entities: bool | None = Field(
        description="A flag indicating whether to take snapshots of raw entities.",
        default=None,
    )
    top_level_nodes: bool | None = Field(
        description="A flag indicating whether to take snapshots of top-level nodes.",
        default=None,
    )
