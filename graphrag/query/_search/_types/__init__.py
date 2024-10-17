# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

import typing

from ._search import (
    Choice,
    Message,
    SearchResult,
    Usage,
)
from ._search_chunk import (
    ChunkChoice,
    Delta,
    SearchResultChunk,
)
from ._search_chunk_verbose import SearchResultChunkVerbose
from ._search_verbose import SearchResultVerbose
from .. import _context

__all__ = [
    "SearchResult",
    "Choice",
    "Message",
    "Usage",
    "SearchResultChunk",
    "ChunkChoice",
    "Delta",
    "SearchResultChunkVerbose",
    "SearchResultVerbose",
]

SearchResult_T: typing.TypeAlias = typing.Union[SearchResult, SearchResultVerbose]

StreamSearchResult_T: typing.TypeAlias = typing.Generator[
    typing.Union[SearchResultChunk, SearchResultChunkVerbose], None, None
]

AsyncStreamSearchResult_T: typing.TypeAlias = typing.AsyncGenerator[
    typing.Union[SearchResultChunk, SearchResultChunkVerbose], None
]

ConversationHistory_T: typing.TypeAlias = typing.Union[
    _context.ConversationHistory,
    typing.List[typing.Dict[typing.Literal["role", "content"], str]],
    None,
]
