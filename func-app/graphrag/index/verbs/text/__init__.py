# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The Indexing Engine text package root."""

from .chunk.text_chunk import chunk
from .embed import text_embed
from .replace import replace
from .split import text_split
from .translate import text_translate

__all__ = [
    "chunk",
    "replace",
    "text_embed",
    "text_split",
    "text_translate",
]
