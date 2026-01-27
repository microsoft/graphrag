# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'TokenChunker' class."""

from collections.abc import Callable
from typing import Any

from graphrag_chunking.chunker import Chunker
from graphrag_chunking.create_chunk_results import create_chunk_results
from graphrag_chunking.text_chunk import TextChunk


class TokenChunker(Chunker):
    """A chunker that splits text into token-based chunks."""

    def __init__(
        self,
        size: int,
        overlap: int,
        encode: Callable[[str], list[int]],
        decode: Callable[[list[int]], str],
        **kwargs: Any,
    ) -> None:
        """Create a token chunker instance."""
        self._size = size
        self._overlap = overlap
        self._encode = encode
        self._decode = decode

    def chunk(
        self, text: str, transform: Callable[[str], str] | None = None
    ) -> list[TextChunk]:
        """Chunk the text into token-based chunks."""
        chunks = split_text_on_tokens(
            text,
            chunk_size=self._size,
            chunk_overlap=self._overlap,
            encode=self._encode,
            decode=self._decode,
        )
        return create_chunk_results(chunks, transform=transform, encode=self._encode)


def split_text_on_tokens(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
    encode: Callable[[str], list[int]],
    decode: Callable[[list[int]], str],
) -> list[str]:
    """Split a single text and return chunks using the tokenizer."""
    result = []
    input_tokens = encode(text)

    start_idx = 0
    cur_idx = min(start_idx + chunk_size, len(input_tokens))
    chunk_tokens = input_tokens[start_idx:cur_idx]

    while start_idx < len(input_tokens):
        chunk_text = decode(list(chunk_tokens))
        result.append(chunk_text)  # Append chunked text as string
        if cur_idx == len(input_tokens):
            break
        start_idx += chunk_size - chunk_overlap
        cur_idx = min(start_idx + chunk_size, len(input_tokens))
        chunk_tokens = input_tokens[start_idx:cur_idx]

    return result
