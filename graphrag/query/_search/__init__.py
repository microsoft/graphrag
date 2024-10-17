# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

import importlib
import typing

from ._context import (
    BaseContextBuilder,
    BaseContextLoader,
    ConversationHistory,
    ConversationRole,
    ConversationTurn,
    GlobalContextBuilder,
    GlobalContextLoader,
    LocalContextBuilder,
    LocalContextLoader,
)
from ._engine import (
    AsyncGlobalSearchEngine,
    AsyncLocalSearchEngine,
    AsyncQueryEngine,
    GlobalSearchEngine,
    LocalSearchEngine,
    QueryEngine,
)
from ._llm import (
    AsyncChatLLM,
    AsyncEmbedding,
    BaseAsyncChatLLM,
    BaseAsyncEmbedding,
    BaseChatLLM,
    BaseEmbedding,
    ChatLLM,
    Embedding,
)
from ._model import (
    Community,
    CommunityReport,
    Covariate,
    Document,
    Entity,
    Identified,
    Named,
    Relationship,
    TextUnit,
)
from ._types import (
    SearchResult, 
    SearchResultChunk,
    SearchResultChunkVerbose, 
    SearchResultVerbose,
)

__all__ = [
    "AsyncQueryEngine",
    "QueryEngine",
    "BaseContextBuilder",
    "GlobalContextBuilder",
    "LocalContextBuilder",
    "ConversationHistory",
    "ConversationRole",
    "ConversationTurn",
    "BaseContextLoader",
    "GlobalContextLoader",
    "LocalContextLoader",
    "AsyncGlobalSearchEngine",
    "AsyncLocalSearchEngine",
    "GlobalSearchEngine",
    "LocalSearchEngine",
    "AsyncChatLLM",
    "AsyncEmbedding",
    "BaseAsyncChatLLM",
    "BaseAsyncEmbedding",
    "BaseChatLLM",
    "BaseEmbedding",
    "ChatLLM",
    "Embedding",
    "Community",
    "CommunityReport",
    "Covariate",
    "Document",
    "Entity",
    "Identified",
    "Named",
    "Relationship",
    "TextUnit",
    "SearchResult",
    "SearchResultChunk",
    "SearchResultChunkVerbose",
    "SearchResultVerbose",
]


# Copied from https://peps.python.org/pep-0562/
def __getattr__(name: str) -> typing.Any:
    if name in __all__:
        return importlib.import_module("." + name, __name__)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
