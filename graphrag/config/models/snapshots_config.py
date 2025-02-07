# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

import graphrag.config.defaults as defs


class SnapshotsConfig(BaseModel):
    """Configuration section for snapshots."""

    embeddings: bool = Field(
        description="A flag indicating whether to take snapshots of embeddings.",
        default=defs.SNAPSHOTS_EMBEDDINGS,
    )
    graphml: bool = Field(
        description="A flag indicating whether to take snapshots of GraphML.",
        default=defs.SNAPSHOTS_GRAPHML,
    )
