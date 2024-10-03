# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The Indexing Engine text package root."""

from .chunk.text_chunk import chunk
from .embed import text_embed

__all__ = [
    "chunk",
    "text_embed",
]
