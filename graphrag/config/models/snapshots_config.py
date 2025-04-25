# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

from graphrag.config.defaults import graphrag_config_defaults


class SnapshotsConfig(BaseModel):
    """Configuration section for snapshots."""

    embeddings: bool = Field(
        description="A flag indicating whether to take snapshots of embeddings.",
        default=graphrag_config_defaults.snapshots.embeddings,
    )
    graphml: bool = Field(
        description="A flag indicating whether to take snapshots of GraphML.",
        default=graphrag_config_defaults.snapshots.graphml,
    )
    raw_graph: bool = Field(
        description="A flag indicating whether to take snapshots of the raw extracted graph (entities and relationships) before merging.",
        default=graphrag_config_defaults.snapshots.raw_graph,
    )
