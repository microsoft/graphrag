# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'TextChunk' model."""

from dataclasses import dataclass


@dataclass
class TextChunk:
    """Text chunk class definition."""

    text_chunk: str
    source_doc_indices: list[int]
    n_tokens: int | None = None


ChunkInput = str | list[str] | list[tuple[str, str]]
"""Input to a chunking strategy. Can be a string, a list of strings, or a list of tuples of (id, text)."""
