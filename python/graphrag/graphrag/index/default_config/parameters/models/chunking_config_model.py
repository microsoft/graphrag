#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""Parameterization settings for the default configuration."""
from pydantic import BaseModel, Field


class ChunkingConfigModel(BaseModel):
    """Configuration section for chunking."""

    size: int | None = Field(description="The chunk size to use.", default=None)
    overlap: int | None = Field(description="The chunk overlap to use.", default=None)
    group_by_columns: list[str] | None = Field(
        description="The chunk by columns to use.", default=None
    )
    strategy: dict | None = Field(
        description="The chunk strategy to use, overriding the default tokenization strategy",
        default=None,
    )
