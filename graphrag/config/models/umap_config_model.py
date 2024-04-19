# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

from graphrag.config.defaults import DEFAULT_UMAP_ENABLED


class UmapConfigModel(BaseModel):
    """Configuration section for UMAP."""

    enabled: bool = Field(
        description="A flag indicating whether to enable UMAP.",
        default=DEFAULT_UMAP_ENABLED,
    )
