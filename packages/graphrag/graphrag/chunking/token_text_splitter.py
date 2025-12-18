# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'TokenTextSplitter' class and 'split_text_on_tokens' function."""

import logging
from abc import ABC
from collections.abc import Callable
from typing import cast

import pandas as pd

from graphrag.tokenizer.tokenizer import Tokenizer

EncodedText = list[int]
DecodeFn = Callable[[EncodedText], str]
EncodeFn = Callable[[str], EncodedText]
LengthFn = Callable[[str], int]

logger = logging.getLogger(__name__)


class TokenTextSplitter(ABC):
    """Token text splitter class definition."""

    _chunk_size: int
    _chunk_overlap: int

    def __init__(
        self,
        tokenizer: Tokenizer,
        # based on OpenAI embedding chunk size limits
        # https://devblogs.microsoft.com/azure-sql/embedding-models-and-dimensions-optimizing-the-performance-resource-usage-ratio/
        chunk_size: int = 8191,
        chunk_overlap: int = 100,
    ):
        """Init method definition."""
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._tokenizer = tokenizer

    def num_tokens(self, text: str) -> int:
        """Return the number of tokens in a string."""
        return self._tokenizer.num_tokens(text)

    def split_text(self, text: str) -> list[str]:
        """Split text method."""
        if cast("bool", pd.isna(text)) or text == "":
            return []
        if not isinstance(text, str):
            msg = f"Attempting to split a non-string value, actual is {type(text)}"
            raise TypeError(msg)

        return split_text_on_tokens(
            text,
            chunk_overlap=self._chunk_overlap,
            tokens_per_chunk=self._chunk_size,
            decode=self._tokenizer.decode,
            encode=self._tokenizer.encode,
        )


def split_text_on_tokens(
    text: str,
    tokens_per_chunk: int,
    chunk_overlap: int,
    encode: EncodeFn,
    decode: DecodeFn,
) -> list[str]:
    """Split a single text and return chunks using the tokenizer."""
    result = []
    input_tokens = encode(text)

    start_idx = 0
    cur_idx = min(start_idx + tokens_per_chunk, len(input_tokens))
    chunk_tokens = input_tokens[start_idx:cur_idx]

    while start_idx < len(input_tokens):
        chunk_text = decode(list(chunk_tokens))
        result.append(chunk_text)  # Append chunked text as string
        if cur_idx == len(input_tokens):
            break
        start_idx += tokens_per_chunk - chunk_overlap
        cur_idx = min(start_idx + tokens_per_chunk, len(input_tokens))
        chunk_tokens = input_tokens[start_idx:cur_idx]

    return result
