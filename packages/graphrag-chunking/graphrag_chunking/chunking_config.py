# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, ConfigDict, Field

from graphrag_chunking.chunk_strategy_type import ChunkerType


class ChunkingConfig(BaseModel):
    """Configuration section for chunking."""

    model_config = ConfigDict(extra="allow")
    """Allow extra fields to support custom cache implementations."""

    type: str = Field(
        description="The chunking type to use.",
        default=ChunkerType.Tokens,
    )
    encoding_model: str | None = Field(
        description="The encoding model to use.",
        default=None,
    )
    size: int = Field(
        description="The chunk size to use.",
        default=1200,
    )
    overlap: int = Field(
        description="The chunk overlap to use.",
        default=100,
    )
    prepend_metadata: list[str] | None = Field(
        description="Metadata fields from the source document to prepend on each chunk.",
        default=None,
    )
