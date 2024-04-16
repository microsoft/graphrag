# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

from graphrag.index.default_config.parameters.defaults import DEFAULT_UMAP_ENABLED


class UmapConfigModel(BaseModel):
    """Configuration section for UMAP."""

    enabled: bool | None = Field(
        description="A flag indicating whether to enable UMAP.",
        default=DEFAULT_UMAP_ENABLED,
    )
