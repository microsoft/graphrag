# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The Indexing Engine text chunk package root."""

from graphrag.index.operations.chunk_text.chunk_text import (
    ChunkStrategy,
    ChunkStrategyType,
    chunk_text,
)

__all__ = ["ChunkStrategy", "ChunkStrategyType", "chunk_text"]
