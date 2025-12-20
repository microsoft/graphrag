# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'SentenceChunker' class."""

from typing import Any

import nltk

from graphrag.chunking.bootstrap_nltk import bootstrap
from graphrag.chunking.chunker import Chunker
from graphrag.chunking.chunking_document import ChunkingDocument


class SentenceChunker(Chunker):
    """A chunker that splits text into sentence-based chunks."""

    def __init__(self, prepend_metadata: bool = False, **kwargs: Any) -> None:
        """Create a sentence chunker instance."""
        self._prepend_metadata = prepend_metadata
        bootstrap()

    def chunk(
        self, document: ChunkingDocument, metadata: dict | None = None
    ) -> list[str]:
        """Chunk the text into sentence-based chunks."""
        text = str(document)
        chunks = nltk.sent_tokenize(text)

        if self._prepend_metadata and metadata is not None:
            metadata_str = ".\n".join(f"{k}: {v}" for k, v in metadata.items()) + ".\n"
            chunks = [metadata_str + chunk for chunk in chunks]
        return chunks
