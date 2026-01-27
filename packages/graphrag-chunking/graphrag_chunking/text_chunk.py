# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The TextChunk dataclass."""

from dataclasses import dataclass


@dataclass
class TextChunk:
    """Result of chunking a document."""

    original: str
    """Raw original text chunk before any transformation."""

    text: str
    """The final text content of this chunk."""

    index: int
    """Zero-based index of this chunk within the source document."""

    start_char: int
    """Character index where the raw chunk text begins in the source document."""

    end_char: int
    """Character index where the raw chunk text ends in the source document."""

    token_count: int | None = None
    """Number of tokens in the final chunk text, if computed."""
