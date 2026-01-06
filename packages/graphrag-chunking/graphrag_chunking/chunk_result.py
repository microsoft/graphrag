# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The ChunkResult dataclass."""

from dataclasses import dataclass


@dataclass
class ChunkResult:
    """Result of chunking a document."""

    text: str
    index: int
    start_char: int
    end_char: int
    token_count: int | None = None
