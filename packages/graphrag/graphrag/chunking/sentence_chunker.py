# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'SentenceChunker' class."""

from typing import Any

import nltk

from graphrag.chunking.bootstrap_nltk import bootstrap
from graphrag.chunking.chunker import Chunker


class SentenceChunker(Chunker):
    """A chunker that splits text into sentence-based chunks."""

    def __init__(self, **kwargs: Any) -> None:
        """Create a sentence chunker instance."""
        bootstrap()

    def chunk(self, text) -> list[str]:
        """Chunk the text into sentence-based chunks."""
        return nltk.sent_tokenize(text)
