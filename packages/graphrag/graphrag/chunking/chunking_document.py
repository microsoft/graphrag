# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing the 'Chunker' class."""

from abc import ABC, abstractmethod
from typing import Any


class ChunkingDocument(ABC):
    """Abstract base class for documents that need to be chunked. If you want to use a text-based chunker, ensure __str__ is implemented."""

    @abstractmethod
    def __init__(self, **kwargs: Any) -> None:
        """Create a chunking document instance."""
