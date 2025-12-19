# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'SentenceChunker' class."""

import json
from typing import Any

import nltk

from graphrag.chunking.bootstrap_nltk import bootstrap
from graphrag.chunking.chunker import Chunker


class SentenceChunker(Chunker):
    """A chunker that splits text into sentence-based chunks."""

    def __init__(self, prepend_metadata: bool = False, **kwargs: Any) -> None:
        """Create a sentence chunker instance."""
        self._prepend_metadata = prepend_metadata
        bootstrap()

    def chunk(self, text: str, metadata: str | dict | None = None) -> list[str]:
        """Chunk the text into sentence-based chunks."""
        chunks = nltk.sent_tokenize(text)

        if self._prepend_metadata and metadata is not None:
            line_delimiter = ".\n"
            metadata_str = ""
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
            if isinstance(metadata, dict):
                metadata_str = (
                    line_delimiter.join(f"{k}: {v}" for k, v in metadata.items())
                    + line_delimiter
                )
            chunks = [metadata_str + chunk for chunk in chunks]
        return chunks
