# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'SummarizedDescriptionResult' model."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any, NamedTuple

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks

StrategyConfig = dict[str, Any]


@dataclass
class SummarizedDescriptionResult:
    """Entity summarization result class definition."""

    id: str | tuple[str, str]
    description: str


SummarizationStrategy = Callable[
    [
        str | tuple[str, str],
        list[str],
        WorkflowCallbacks,
        PipelineCache,
        StrategyConfig,
    ],
    Awaitable[SummarizedDescriptionResult],
]


class DescriptionSummarizeRow(NamedTuple):
    """DescriptionSummarizeRow class definition."""

    graph: Any


class SummarizeStrategyType(str, Enum):
    """SummarizeStrategyType class definition."""

    graph_intelligence = "graph_intelligence"

    def __repr__(self):
        """Get a string representation."""
        return f'"{self.value}"'
