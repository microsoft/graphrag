# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

import graphrag.config.defaults as defs


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
    strategy: dict | None = Field(
        description="The chunk strategy to use, overriding the default tokenization strategy",
        default=None,
    )
    encoding_model: str | None = Field(
        default=None, description="The encoding model to use."
    )

    def resolved_strategy(self, encoding_model: str) -> dict:
        """Get the resolved chunking strategy."""
        from graphrag.index.verbs.text.chunk import ChunkStrategyType

        return self.strategy or {
            "type": ChunkStrategyType.tokens,
            "chunk_size": self.size,
            "chunk_overlap": self.overlap,
            "group_by_columns": self.group_by_columns,
            "encoding_name": self.encoding_model or encoding_model,
        }
