# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing chunk strategies."""

from collections.abc import Iterable
from typing import Any

import nltk
import tiktoken

from graphrag.config.models.chunking_config import ChunkingConfig
from graphrag.index.operations.chunk_text.typing import TextChunk
from graphrag.index.text_splitting.text_splitting import (
    Tokenizer,
    split_multiple_texts_on_tokens,
)
from graphrag.logger.progress import ProgressTicker


def run_tokens(
    input: list[str],
    config: ChunkingConfig,
    tick: ProgressTicker,
    metadata: dict[str, Any] | None = None,
    line_delimiter: str = ".\n",
) -> Iterable[TextChunk]:
    """Chunks text into chunks based on encoding tokens."""
    tokens_per_chunk = config.size
    chunk_overlap = config.overlap
    encoding_name = config.encoding_model
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
        line_delimiter,
        metadata,
    )


def run_sentences(
    input: list[str],
    _config: ChunkingConfig,
    tick: ProgressTicker,
    metadata: dict[str, Any] | None = None,
    line_delimiter: str = ".\n",
) -> Iterable[TextChunk]:
    """Chunks text into multiple parts by sentence."""
    for doc_idx, text in enumerate(input):
        sentences = nltk.sent_tokenize(text)
        for sentence in sentences:
            metadata_str = ""
            if metadata is not None and len(metadata) > 0:
                metadata_str = line_delimiter.join([
                    f"{k}: {v}" for k, v in metadata.items()
                ])
            sentence = (
                f"{metadata_str}{line_delimiter}{sentence}"
                if metadata_str
                else sentence
            )
            yield TextChunk(
                text_chunk=sentence,
                source_doc_indices=[doc_idx],
            )
        tick(1)
