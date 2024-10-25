# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'Document' and 'EntityExtractionResult' models."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import networkx as nx
from datashaper import VerbCallbacks

from graphrag.index.cache.pipeline_cache import PipelineCache

ExtractedEntity = dict[str, Any]
StrategyConfig = dict[str, Any]
EntityTypes = list[str]


@dataclass
class Document:
    """Document class definition."""

    text: str
    id: str


@dataclass
class EntityExtractionResult:
    """Entity extraction result class definition."""

    entities: list[ExtractedEntity]
    graph: nx.Graph | None


EntityExtractStrategy = Callable[
    [
        list[Document],
        EntityTypes,
        VerbCallbacks,
        PipelineCache,
        StrategyConfig,
    ],
    Awaitable[EntityExtractionResult],
]
