# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'TokenChunker' class."""

from typing import Any

from graphrag.chunking.chunker import Chunker
from graphrag.chunking.token_text_splitter import (
    TokenTextSplitter,
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
        self._text_splitter = TokenTextSplitter(
            chunk_size=size,
            chunk_overlap=overlap,
            tokenizer=get_tokenizer(encoding_model=encoding_model),
        )

    def chunk(self, text: str) -> list[str]:
        """Chunk the text into token-based chunks."""
        return self._text_splitter.split_text(text)
