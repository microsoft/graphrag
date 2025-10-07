# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing the 'Tokenizer', 'TextSplitter', 'NoopTextSplitter' and 'TokenTextSplitter' models."""

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any, cast

import pandas as pd

from graphrag.index.operations.chunk_text.typing import TextChunk
from graphrag.logger.progress import ProgressTicker
from graphrag.tokenizer.get_tokenizer import get_tokenizer
from graphrag.tokenizer.tokenizer import Tokenizer

EncodedText = list[int]
DecodeFn = Callable[[EncodedText], str]
EncodeFn = Callable[[str], EncodedText]
LengthFn = Callable[[str], int]

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TokenChunkerOptions:
    """TokenChunkerOptions data class."""

    chunk_overlap: int
    """Overlap in tokens between chunks"""
    tokens_per_chunk: int
    """Maximum number of tokens per chunk"""
    decode: DecodeFn
    """ Function to decode a list of token ids to a string"""
    encode: EncodeFn
    """ Function to encode a string to a list of token ids"""


class TextSplitter(ABC):
    """Text splitter class definition."""

    _chunk_size: int
    _chunk_overlap: int
    _length_function: LengthFn
    _keep_separator: bool
    _add_start_index: bool
    _strip_whitespace: bool

    def __init__(
        self,
        # based on text-ada-002-embedding max input buffer length
        # https://platform.openai.com/docs/guides/embeddings/second-generation-models
        chunk_size: int = 8191,
        chunk_overlap: int = 100,
        length_function: LengthFn = len,
        keep_separator: bool = False,
        add_start_index: bool = False,
        strip_whitespace: bool = True,
    ):
        """Init method definition."""
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._length_function = length_function
        self._keep_separator = keep_separator
        self._add_start_index = add_start_index
        self._strip_whitespace = strip_whitespace

    @abstractmethod
    def split_text(self, text: str | list[str]) -> Iterable[str]:
        """Split text method definition."""


class NoopTextSplitter(TextSplitter):
    """Noop text splitter class definition."""

    def split_text(self, text: str | list[str]) -> Iterable[str]:
        """Split text method definition."""
        return [text] if isinstance(text, str) else text


class TokenTextSplitter(TextSplitter):
    """Token text splitter class definition."""

    def __init__(
        self,
        tokenizer: Tokenizer | None = None,
        **kwargs: Any,
    ):
        """Init method definition."""
        super().__init__(**kwargs)
        self._tokenizer = tokenizer or get_tokenizer()

    def num_tokens(self, text: str) -> int:
        """Return the number of tokens in a string."""
        return self._tokenizer.num_tokens(text)

    def split_text(self, text: str | list[str]) -> list[str]:
        """Split text method."""
        if isinstance(text, list):
            text = " ".join(text)
        elif cast("bool", pd.isna(text)) or text == "":
            return []
        if not isinstance(text, str):
            msg = f"Attempting to split a non-string value, actual is {type(text)}"
            raise TypeError(msg)

        token_chunker_options = TokenChunkerOptions(
            chunk_overlap=self._chunk_overlap,
            tokens_per_chunk=self._chunk_size,
            decode=self._tokenizer.decode,
            encode=self._tokenizer.encode,
        )

        return split_single_text_on_tokens(text=text, tokenizer=token_chunker_options)


def split_single_text_on_tokens(text: str, tokenizer: TokenChunkerOptions) -> list[str]:
    """Split a single text and return chunks using the tokenizer."""
    result = []
    input_ids = tokenizer.encode(text)

    start_idx = 0
    cur_idx = min(start_idx + tokenizer.tokens_per_chunk, len(input_ids))
    chunk_ids = input_ids[start_idx:cur_idx]

    while start_idx < len(input_ids):
        chunk_text = tokenizer.decode(list(chunk_ids))
        result.append(chunk_text)  # Append chunked text as string
        if cur_idx == len(input_ids):
            break
        start_idx += tokenizer.tokens_per_chunk - tokenizer.chunk_overlap
        cur_idx = min(start_idx + tokenizer.tokens_per_chunk, len(input_ids))
        chunk_ids = input_ids[start_idx:cur_idx]

    return result


# Adapted from - https://github.com/langchain-ai/langchain/blob/77b359edf5df0d37ef0d539f678cf64f5557cb54/libs/langchain/langchain/text_splitter.py#L471
# So we could have better control over the chunking process
def split_multiple_texts_on_tokens(
    texts: list[str], tokenizer: TokenChunkerOptions, tick: ProgressTicker
) -> list[TextChunk]:
    """Split multiple texts and return chunks with metadata using the tokenizer."""
    result = []
    mapped_ids = []

    for source_doc_idx, text in enumerate(texts):
        encoded = tokenizer.encode(text)
        if tick:
            tick(1)  # Track progress if tick callback is provided
        mapped_ids.append((source_doc_idx, encoded))

    input_ids = [
        (source_doc_idx, id) for source_doc_idx, ids in mapped_ids for id in ids
    ]

    start_idx = 0
    cur_idx = min(start_idx + tokenizer.tokens_per_chunk, len(input_ids))
    chunk_ids = input_ids[start_idx:cur_idx]

    while start_idx < len(input_ids):
        chunk_text = tokenizer.decode([id for _, id in chunk_ids])
        doc_indices = list({doc_idx for doc_idx, _ in chunk_ids})
        result.append(TextChunk(chunk_text, doc_indices, len(chunk_ids)))
        if cur_idx == len(input_ids):
            break
        start_idx += tokenizer.tokens_per_chunk - tokenizer.chunk_overlap
        cur_idx = min(start_idx + tokenizer.tokens_per_chunk, len(input_ids))
        chunk_ids = input_ids[start_idx:cur_idx]

    return result
