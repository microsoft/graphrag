# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

from graphrag.index.default_config.parameters.defaults import (
    DEFAULT_MAX_CLUSTER_SIZE,
)


class ClusterGraphConfigModel(BaseModel):
    """Configuration section for clustering graphs."""

    max_cluster_size: int | None = Field(
        description="The maximum cluster size to use.", default=DEFAULT_MAX_CLUSTER_SIZE
    )
    strategy: dict | None = Field(
        description="The cluster strategy to use.", default=None
    )
