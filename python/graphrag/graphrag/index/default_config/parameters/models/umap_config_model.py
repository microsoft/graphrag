# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field


class UmapConfigModel(BaseModel):
    """Configuration section for UMAP."""

    enabled: bool | None = Field(
        description="A flag indicating whether to enable UMAP.", default=None
    )
