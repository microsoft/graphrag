# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

from graphrag.index.default_config.parameters.defaults import (
    DEFAULT_CHUNK_GROUP_BY_COLUMNS,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
)


class ChunkingConfigModel(BaseModel):
    """Configuration section for chunking."""

    size: int | None = Field(
        description="The chunk size to use.", default=DEFAULT_CHUNK_SIZE
    )
    overlap: int | None = Field(
        description="The chunk overlap to use.", default=DEFAULT_CHUNK_OVERLAP
    )
    group_by_columns: list[str] | None = Field(
        description="The chunk by columns to use.",
        default=DEFAULT_CHUNK_GROUP_BY_COLUMNS,
    )
    strategy: dict | None = Field(
        description="The chunk strategy to use, overriding the default tokenization strategy",
        default=None,
    )
