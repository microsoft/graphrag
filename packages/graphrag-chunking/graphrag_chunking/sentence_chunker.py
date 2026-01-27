# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'SentenceChunker' class."""

from collections.abc import Callable
from typing import Any

import nltk

from graphrag_chunking.bootstrap_nltk import bootstrap
from graphrag_chunking.chunker import Chunker
from graphrag_chunking.create_chunk_results import create_chunk_results
from graphrag_chunking.text_chunk import TextChunk


class SentenceChunker(Chunker):
    """A chunker that splits text into sentence-based chunks."""

    def __init__(
        self, encode: Callable[[str], list[int]] | None = None, **kwargs: Any
    ) -> None:
        """Create a sentence chunker instance."""
        self._encode = encode
        bootstrap()

    def chunk(
        self, text: str, transform: Callable[[str], str] | None = None
    ) -> list[TextChunk]:
        """Chunk the text into sentence-based chunks."""
        sentences = nltk.sent_tokenize(text.strip())
        results = create_chunk_results(
            sentences, transform=transform, encode=self._encode
        )
        # nltk sentence tokenizer may trim whitespace, so we need to adjust start/end chars
        for index, result in enumerate(results):
            txt = result.text
            start = result.start_char
            actual_start = text.find(txt, start)
            delta = actual_start - start
            if delta > 0:
                result.start_char += delta
                result.end_char += delta
                # bump the next to keep the start check from falling too far behind
                if index < len(results) - 1:
                    results[index + 1].start_char += delta
                    results[index + 1].end_char += delta
        return results
