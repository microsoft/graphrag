#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""The Indexing Engine text chunk package root."""
from .text_chunk import ChunkStrategy, ChunkStrategyType, chunk

__all__ = ["chunk", "ChunkStrategy", "ChunkStrategyType"]
