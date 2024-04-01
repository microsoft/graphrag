#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""The Indexing Engine text package root."""
from .chunk.text_chunk import chunk
from .embed import text_embed
from .replace import replace
from .split import text_split
from .translate import text_translate

__all__ = [
    "chunk",
    "text_embed",
    "replace",
    "text_split",
    "text_translate",
]
