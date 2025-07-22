# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'TextChunk' model."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass

from graphrag.config.models.chunking_config import ChunkingConfig
from graphrag.logger.progress import ProgressTicker


@dataclass
class TextChunk:
    """Text chunk class definition."""

    text_chunk: str
    source_doc_indices: list[int]
    n_tokens: int | None = None


ChunkInput = str | list[str] | list[tuple[str, str]]
"""Input to a chunking strategy. Can be a string, a list of strings, or a list of tuples of (id, text)."""

ChunkStrategy = Callable[
    [list[str], ChunkingConfig, ProgressTicker], Iterable[TextChunk]
]
