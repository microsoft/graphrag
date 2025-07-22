# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

from graphrag.config.defaults import graphrag_config_defaults
from graphrag.config.enums import ChunkStrategyType


class ChunkingConfig(BaseModel):
    """Configuration section for chunking."""

    size: int = Field(
        description="The chunk size to use.",
        default=graphrag_config_defaults.chunks.size,
    )
    overlap: int = Field(
        description="The chunk overlap to use.",
        default=graphrag_config_defaults.chunks.overlap,
    )
    group_by_columns: list[str] = Field(
        description="The chunk by columns to use.",
        default=graphrag_config_defaults.chunks.group_by_columns,
    )
    strategy: ChunkStrategyType = Field(
        description="The chunking strategy to use.",
        default=graphrag_config_defaults.chunks.strategy,
    )
    encoding_model: str = Field(
        description="The encoding model to use.",
        default=graphrag_config_defaults.chunks.encoding_model,
    )
    prepend_metadata: bool = Field(
        description="Prepend metadata into each chunk.",
        default=graphrag_config_defaults.chunks.prepend_metadata,
    )
    chunk_size_includes_metadata: bool = Field(
        description="Count metadata in max tokens.",
        default=graphrag_config_defaults.chunks.chunk_size_includes_metadata,
    )
