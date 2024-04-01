#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""Parameterization settings for the default configuration."""
from pydantic import BaseModel, Field


class UmapConfigModel(BaseModel):
    """Configuration section for UMAP."""

    enabled: bool | None = Field(
        description="A flag indicating whether to enable UMAP.", default=None
    )
