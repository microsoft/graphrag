# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'TokenChunker' class."""

from collections.abc import Callable
from typing import Any

from graphrag_common.types.tokenizer import Tokenizer

from graphrag.chunking.chunker import Chunker
from graphrag.chunking.chunking_document import ChunkingDocument

EncodedText = list[int]
DecodeFn = Callable[[EncodedText], str]
EncodeFn = Callable[[str], EncodedText]


class TokenChunker(Chunker):
    """A chunker that splits text into token-based chunks."""

    def __init__(
        self,
        size: int,
        overlap: int,
        tokenizer: Tokenizer,
        prepend_metadata: bool = False,
        **kwargs: Any,
    ) -> None:
        """Create a token chunker instance."""
        self._size = size
        self._overlap = overlap
        self._prepend_metadata = prepend_metadata
        self._tokenizer = tokenizer

    def chunk(
        self, document: ChunkingDocument, metadata: dict | None = None
    ) -> list[str]:
        """Chunk the text into token-based chunks."""
        # we have to create and measure the metadata first to account for the length when chunking
        text = str(document)

        chunks = split_text_on_tokens(
            text,
            chunk_size=self._size,
            chunk_overlap=self._overlap,
            encode=self._tokenizer.encode,
            decode=self._tokenizer.decode,
        )

        if self._prepend_metadata and metadata is not None:
            metadata_str = ".\n".join(f"{k}: {v}" for k, v in metadata.items()) + ".\n"
            chunks = [metadata_str + chunk for chunk in chunks]

        return chunks


def split_text_on_tokens(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
    encode: EncodeFn,
    decode: DecodeFn,
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
