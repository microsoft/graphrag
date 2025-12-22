# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing the 'Chunker' class."""

from abc import ABC, abstractmethod
from typing import Any

from graphrag_chunking.chunk_result import ChunkResult


class Chunker(ABC):
    """Abstract base class for document chunkers."""

    @abstractmethod
    def __init__(self, **kwargs: Any) -> None:
        """Create a chunker instance."""

    @abstractmethod
    def chunk(self, text: str) -> list[ChunkResult]:
        """Chunk method definition."""
