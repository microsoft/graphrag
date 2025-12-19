# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

from graphrag.chunking.chunk_strategy_type import ChunkStrategyType
from graphrag.config.defaults import graphrag_config_defaults


class ChunkingConfig(BaseModel):
    """Configuration section for chunking."""

    strategy: str = Field(
        description="The chunking strategy to use.",
        default=ChunkStrategyType.tokens,
    )
    size: int = Field(
        description="The chunk size to use.",
        default=graphrag_config_defaults.chunks.size,
    )
    overlap: int = Field(
        description="The chunk overlap to use.",
        default=graphrag_config_defaults.chunks.overlap,
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
