# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

import typing

from ._search import _types
from ._search._engine import _base_engine
from ._search._llm import _types as _llm_types

MessageParam_T: typing.TypeAlias = _llm_types.MessageParam_T

__all__ = [
    'Logger',
    'Response',
    'ResponseVerbose',
    'ResponseChunk',
    'ResponseChunkVerbose',
    'MessageParam_T',
    'Response_T',
    'StreamResponse_T',
    'AsyncStreamResponse_T',
]

Logger: typing.TypeAlias = _base_engine.Logger
Response: typing.TypeAlias = _types.SearchResult
ResponseVerbose: typing.TypeAlias = _types.SearchResultVerbose
ResponseChunk: typing.TypeAlias = _types.SearchResultChunk
ResponseChunkVerbose: typing.TypeAlias = _types.SearchResultChunkVerbose

Response_T: typing.TypeAlias = typing.Union[Response, ResponseVerbose]
_Response_Chunk_T: typing.TypeAlias = typing.Union[ResponseChunk, ResponseChunkVerbose]
StreamResponse_T: typing.TypeAlias = typing.Iterator[_Response_Chunk_T]
AsyncStreamResponse_T: typing.TypeAlias = typing.AsyncIterator[_Response_Chunk_T]
