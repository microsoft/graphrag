# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing the 'Tokenizer', 'TextSplitter', 'NoopTextSplitter' and 'TokenTextSplitter' models."""

import json
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable, Collection, Iterable
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal, cast

import pandas as pd
import tiktoken

from graphrag.index.utils import num_tokens_from_string

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
        encoding_name: str = "cl100k_base",
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
        if cast(bool, pd.isna(text)) or text == "":
            return []
        if isinstance(text, list):
            text = " ".join(text)
        if not isinstance(text, str):
            msg = f"Attempting to split a non-string value, actual is {type(text)}"
            raise TypeError(msg)

        tokenizer = Tokenizer(
            chunk_overlap=self._chunk_overlap,
            tokens_per_chunk=self._chunk_size,
            decode=self._tokenizer.decode,
            encode=lambda text: self.encode(text),
        )

        return split_text_on_tokens(text=text, tokenizer=tokenizer)


class TextListSplitterType(str, Enum):
    """Enum for the type of the TextListSplitter."""

    DELIMITED_STRING = "delimited_string"
    JSON = "json"


class TextListSplitter(TextSplitter):
    """Text list splitter class definition."""

    def __init__(
        self,
        chunk_size: int,
        splitter_type: TextListSplitterType = TextListSplitterType.JSON,
        input_delimiter: str | None = None,
        output_delimiter: str | None = None,
        model_name: str | None = None,
        encoding_name: str | None = None,
    ):
        """Initialize the TextListSplitter with a chunk size."""
        # Set the chunk overlap to 0 as we use full strings
        super().__init__(chunk_size, chunk_overlap=0)
        self._type = splitter_type
        self._input_delimiter = input_delimiter
        self._output_delimiter = output_delimiter or "\n"
        self._length_function = lambda x: num_tokens_from_string(
            x, model=model_name, encoding_name=encoding_name
        )

    def split_text(self, text: str | list[str]) -> Iterable[str]:
        """Split a string list into a list of strings for a given chunk size."""
        if not text:
            return []

        result: list[str] = []
        current_chunk: list[str] = []

        # Add the brackets
        current_length: int = self._length_function("[]")

        # Input should be a string list joined by a delimiter
        string_list = self._load_text_list(text)

        if len(string_list) == 1:
            return string_list

        for item in string_list:
            # Count the length of the item and add comma
            item_length = self._length_function(f"{item},")

            if current_length + item_length > self._chunk_size:
                if current_chunk and len(current_chunk) > 0:
                    # Add the current chunk to the result
                    self._append_to_result(result, current_chunk)

                    # Start a new chunk
                    current_chunk = [item]
                    # Add 2 for the brackets
                    current_length = item_length
            else:
                # Add the item to the current chunk
                current_chunk.append(item)
                # Add 1 for the comma
                current_length += item_length

        # Add the last chunk to the result
        self._append_to_result(result, current_chunk)

        return result

    def _load_text_list(self, text: str | list[str]):
        """Load the text list based on the type."""
        if isinstance(text, list):
            string_list = text
        elif self._type == TextListSplitterType.JSON:
            string_list = json.loads(text)
        else:
            string_list = text.split(self._input_delimiter)
        return string_list

    def _append_to_result(self, chunk_list: list[str], new_chunk: list[str]):
        """Append the current chunk to the result."""
        if new_chunk and len(new_chunk) > 0:
            if self._type == TextListSplitterType.JSON:
                chunk_list.append(json.dumps(new_chunk, ensure_ascii=False))
            else:
                chunk_list.append(self._output_delimiter.join(new_chunk))


def split_text_on_tokens(*, text: str, tokenizer: Tokenizer) -> list[str]:
    """Split incoming text and return chunks using tokenizer."""
    splits: list[str] = []
    input_ids = tokenizer.encode(text)
    start_idx = 0
    cur_idx = min(start_idx + tokenizer.tokens_per_chunk, len(input_ids))
    chunk_ids = input_ids[start_idx:cur_idx]
    while start_idx < len(input_ids):
        splits.append(tokenizer.decode(chunk_ids))
        start_idx += tokenizer.tokens_per_chunk - tokenizer.chunk_overlap
        cur_idx = min(start_idx + tokenizer.tokens_per_chunk, len(input_ids))
        chunk_ids = input_ids[start_idx:cur_idx]
    return splits
