# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing the 'Chunker' class."""

from abc import ABC, abstractmethod
from typing import Any

from graphrag.chunking.chunking_document import ChunkingDocument


class Chunker(ABC):
    """Abstract base class for text chunkers."""

    @abstractmethod
    def __init__(self, **kwargs: Any) -> None:
        """Create a chunker instance."""

    @abstractmethod
    def chunk(
        self, document: ChunkingDocument, metadata: dict | None = None
    ) -> list[str]:
        """Chunk method definition."""
