# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

import graphrag.config.defaults as defs
from graphrag.config.enums import ChunkStrategyType


class ChunkingConfig(BaseModel):
    """Configuration section for chunking."""

    size: int = Field(description="The chunk size to use.", default=defs.CHUNK_SIZE)
    overlap: int = Field(
        description="The chunk overlap to use.", default=defs.CHUNK_OVERLAP
    )
    group_by_columns: list[str] = Field(
        description="The chunk by columns to use.",
        default=defs.CHUNK_GROUP_BY_COLUMNS,
    )
    strategy: ChunkStrategyType = Field(
        description="The chunking strategy to use.", default=defs.CHUNK_STRATEGY
    )
    encoding_model: str = Field(
        description="The encoding model to use.", default=defs.ENCODING_MODEL
    )
    prepend_metadata: bool = Field(
        description="Prepend metadata into each chunk.",
        default=defs.CHUNK_PREPEND_METADATA,
    )
    chunk_size_includes_metadata: bool = Field(
        description="Count metadata in max tokens.",
        default=defs.CHUNK_SIZE_INCLUDES_METADATA,
    )
