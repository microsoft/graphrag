# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'TokenChunker' class."""

from typing import Any

from graphrag.chunking.chunker import Chunker
from graphrag.index.text_splitting.text_splitting import (
    split_single_text_on_tokens,
)
from graphrag.tokenizer.get_tokenizer import get_tokenizer


class TokenChunker(Chunker):
    """A chunker that splits text into token-based chunks."""

    def __init__(
        self,
        size: int,
        overlap: int,
        encoding_model: str,
        **kwargs: Any,
    ) -> None:
        """Create a token chunker instance."""
        self._size = size
        self._overlap = overlap
        self._encoding_model = encoding_model

    def chunk(self, text: str) -> list[str]:
        """Chunk the text into token-based chunks."""
        tokenizer = get_tokenizer(encoding_model=self._encoding_model)
        return split_single_text_on_tokens(
            text,
            chunk_overlap=self._overlap,
            tokens_per_chunk=self._size,
            encode=tokenizer.encode,
            decode=tokenizer.decode,
        )
