# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'Document' and 'EntityExtractionResult' models."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from datashaper import VerbCallbacks

from graphrag.index.cache import PipelineCache

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
    graphml_graph: str | None


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
