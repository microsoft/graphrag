# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

import graphrag.config.defaults as defs


class UmapConfig(BaseModel):
    """Configuration section for UMAP."""

    enabled: bool = Field(
        description="A flag indicating whether to enable UMAP.",
        default=defs.UMAP_ENABLED,
    )
