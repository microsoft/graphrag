# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing chunk strategies."""

from collections.abc import Iterable
from typing import Any

import nltk
import tiktoken
from datashaper import ProgressTicker

import graphrag.config.defaults as defs
from graphrag.index.operations.chunk_text.typing import TextChunk
from graphrag.index.text_splitting.text_splitting import (
    Tokenizer,
    split_multiple_texts_on_tokens,
)


def run_tokens(
    input: list[str], args: dict[str, Any], tick: ProgressTicker
) -> Iterable[TextChunk]:
    """Chunks text into chunks based on encoding tokens."""
    tokens_per_chunk = args.get("chunk_size", defs.CHUNK_SIZE)
    chunk_overlap = args.get("chunk_overlap", defs.CHUNK_OVERLAP)
    encoding_name = args.get("encoding_name", defs.ENCODING_MODEL)
    enc = tiktoken.get_encoding(encoding_name)

    def encode(text: str) -> list[int]:
        if not isinstance(text, str):
            text = f"{text}"
        return enc.encode(text)

    def decode(tokens: list[int]) -> str:
        return enc.decode(tokens)

    return split_multiple_texts_on_tokens(
        input,
        Tokenizer(
            chunk_overlap=chunk_overlap,
            tokens_per_chunk=tokens_per_chunk,
            encode=encode,
            decode=decode,
        ),
        tick,
    )


def run_sentences(
    input: list[str], _args: dict[str, Any], tick: ProgressTicker
) -> Iterable[TextChunk]:
    """Chunks text into multiple parts by sentence."""
    for doc_idx, text in enumerate(input):
        sentences = nltk.sent_tokenize(text)
        for sentence in sentences:
            yield TextChunk(
                text_chunk=sentence,
                source_doc_indices=[doc_idx],
            )
        tick(1)
