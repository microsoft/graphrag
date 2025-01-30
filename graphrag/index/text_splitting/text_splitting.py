# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing the 'Tokenizer', 'TextSplitter', 'NoopTextSplitter' and 'TokenTextSplitter' models."""

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable, Collection, Iterable
from dataclasses import dataclass
from typing import Any, Literal, cast

import pandas as pd
import tiktoken

import graphrag.config.defaults as defs
from graphrag.index.operations.chunk_text.typing import TextChunk
from graphrag.logger.progress import ProgressTicker

EncodedText = list[int]
DecodeFn = Callable[[EncodedText], str]
EncodeFn = Callable[[str], EncodedText]
LengthFn = Callable[[str], int]

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Tokenizer:
    """Tokenizer data class."""

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

    _allowed_special: Literal["all"] | set[str]
    _disallowed_special: Literal["all"] | Collection[str]

    def __init__(
        self,
        encoding_name: str = defs.ENCODING_MODEL,
        model_name: str | None = None,
        allowed_special: Literal["all"] | set[str] | None = None,
        disallowed_special: Literal["all"] | Collection[str] = "all",
        **kwargs: Any,
    ):
        """Init method definition."""
        super().__init__(**kwargs)
        if model_name is not None:
            try:
                enc = tiktoken.encoding_for_model(model_name)
            except KeyError:
                log.exception("Model %s not found, using %s", model_name, encoding_name)
                enc = tiktoken.get_encoding(encoding_name)
        else:
            enc = tiktoken.get_encoding(encoding_name)
        self._tokenizer = enc
        self._allowed_special = allowed_special or set()
        self._disallowed_special = disallowed_special

    def encode(self, text: str) -> list[int]:
        """Encode the given text into an int-vector."""
        return self._tokenizer.encode(
            text,
            allowed_special=self._allowed_special,
            disallowed_special=self._disallowed_special,
        )

    def num_tokens(self, text: str) -> int:
        """Return the number of tokens in a string."""
        return len(self.encode(text))

    def split_text(self, text: str | list[str]) -> list[str]:
        """Split text method."""
        if isinstance(text, list):
            text = " ".join(text)
        elif cast("bool", pd.isna(text)) or text == "":
            return []
        if not isinstance(text, str):
            msg = f"Attempting to split a non-string value, actual is {type(text)}"
            raise TypeError(msg)

        tokenizer = Tokenizer(
            chunk_overlap=self._chunk_overlap,
            tokens_per_chunk=self._chunk_size,
            decode=self._tokenizer.decode,
            encode=lambda text: self.encode(text),
        )

        return split_single_text_on_tokens(text=text, tokenizer=tokenizer)


def split_single_text_on_tokens(text: str, tokenizer: Tokenizer) -> list[str]:
    """Split a single text and return chunks using the tokenizer."""
    result = []
    input_ids = tokenizer.encode(text)

    start_idx = 0
    cur_idx = min(start_idx + tokenizer.tokens_per_chunk, len(input_ids))
    chunk_ids = input_ids[start_idx:cur_idx]

    while start_idx < len(input_ids):
        chunk_text = tokenizer.decode(list(chunk_ids))
        result.append(chunk_text)  # Append chunked text as string
        start_idx += tokenizer.tokens_per_chunk - tokenizer.chunk_overlap
        cur_idx = min(start_idx + tokenizer.tokens_per_chunk, len(input_ids))
        chunk_ids = input_ids[start_idx:cur_idx]

    return result


def split_multiple_texts_on_tokens(
    texts: list[str],
    tokenizer: Tokenizer,
    tick: ProgressTicker | None = None,
    line_delimiter: str = ".\n",
    metadata: dict[str, Any] | None = None,
) -> list[TextChunk]:
    """Split multiple texts and return chunks with metadata using the tokenizer."""
    result = []
    metadata_str = (
        line_delimiter.join(f"{k}: {v}" for k, v in metadata.items())
        if metadata
        else ""
    )
    metadata_tokens = tokenizer.encode(metadata_str)

    # Adjust tokenizer to account for metadata tokens
    adjusted_tokenizer = Tokenizer(
        chunk_overlap=tokenizer.chunk_overlap,
        tokens_per_chunk=tokenizer.tokens_per_chunk - len(metadata_tokens),
        decode=tokenizer.decode,
        encode=tokenizer.encode,
    )

    input_ids = []
    for source_doc_idx, text in enumerate(texts):
        encoded = adjusted_tokenizer.encode(text)
        if tick:
            tick(1)  # Track progress
        input_ids.extend((source_doc_idx, token) for token in encoded)

    start_idx = 0
    total_tokens = len(input_ids)

    while start_idx < total_tokens:
        cur_idx = min(start_idx + adjusted_tokenizer.tokens_per_chunk, total_tokens)
        chunk_ids = input_ids[start_idx:cur_idx]
        chunk_text = f"{metadata_str}{line_delimiter}" if metadata_str else ""
        chunk_text += adjusted_tokenizer.decode([token for _, token in chunk_ids])

        doc_indices = list({doc_idx for doc_idx, _ in chunk_ids})
        result.append(
            TextChunk(chunk_text, doc_indices, len(chunk_ids) + len(metadata_tokens))
        )

        start_idx += (
            adjusted_tokenizer.tokens_per_chunk - adjusted_tokenizer.chunk_overlap
        )

    return result
