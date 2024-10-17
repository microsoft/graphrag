# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

import importlib
import typing

from . import (
    errors,
    types,
)
from ._client import (
    AsyncGraphRAGClient,
    GraphRAGClient,
)
from ._config import (
    ChatLLMConfig,
    ContextConfig,
    EmbeddingConfig,
    GlobalSearchConfig,
    GraphRAGConfig,
    LocalSearchConfig,
    LoggingConfig,
)
from ._search import (
    AsyncGlobalSearchEngine,
    AsyncLocalSearchEngine,
    AsyncQueryEngine,
    BaseContextBuilder,
    GlobalContextBuilder,
    GlobalContextLoader,
    GlobalSearchEngine,
    LocalContextBuilder,
    LocalContextLoader,
    LocalSearchEngine,
    QueryEngine,
    SearchResult,
    SearchResultChunk,
    SearchResultChunkVerbose,
    SearchResultVerbose,
)
from ._version import (
    __title__,
    __version__,
)

__all__ = [
    "errors",
    "types",

    "__title__",
    "__version__",

    "GraphRAGClient",
    "AsyncGraphRAGClient",

    "QueryEngine",
    "AsyncQueryEngine",
    "LocalSearchEngine",
    "GlobalSearchEngine",
    "AsyncLocalSearchEngine",
    "AsyncGlobalSearchEngine",
    "BaseContextBuilder",
    "LocalContextBuilder",
    "GlobalContextBuilder",
    "LocalContextLoader",
    "GlobalContextLoader",
    "SearchResult",
    "SearchResultVerbose",
    "SearchResultChunk",
    "SearchResultChunkVerbose",

    'ChatLLMConfig',
    'EmbeddingConfig',
    'LoggingConfig',
    'ContextConfig',
    'LocalSearchConfig',
    'GlobalSearchConfig',
    'GraphRAGConfig',
]


# Copied from https://peps.python.org/pep-0562/
def __getattr__(name: str) -> typing.Any:
    if name in __all__:
        return importlib.import_module("." + name, __name__)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
