# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing the 'Chunker' class."""

from typing import Any

from graphrag.chunking.chunking_document import ChunkingDocument


class TextChunkingDocument(ChunkingDocument):
    """Represents a basic text document for chunking."""

    def __init__(self, text: str, **kwargs: Any) -> None:
        """Create a chunking document instance."""
        self._text = text

    def __str__(self) -> str:
        """Get the text of the document."""
        return self._text
