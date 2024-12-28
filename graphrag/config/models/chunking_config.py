# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from enum import Enum

from pydantic import BaseModel, Field

import graphrag.config.defaults as defs


class ChunkStrategyType(str, Enum):
    """ChunkStrategy class definition."""

    tokens = "tokens"
    sentence = "sentence"

    def __repr__(self):
        """Get a string representation."""
        return f'"{self.value}"'


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
        description="The chunking strategy to use.", default=ChunkStrategyType.tokens
    )
    encoding_model: str = Field(
        description="The encoding model to use.", default=defs.ENCODING_MODEL
    )
