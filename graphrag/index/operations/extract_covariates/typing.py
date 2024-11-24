# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'Covariate' and 'CovariateExtractionResult' models."""

from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from datashaper import VerbCallbacks

from graphrag.index.cache.pipeline_cache import PipelineCache


@dataclass
class Covariate:
    """Covariate class definition."""

    covariate_type: str | None = None
    subject_id: str | None = None
    object_id: str | None = None
    type: str | None = None
    status: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None
    source_text: list[str] | None = None
    doc_id: str | None = None
    record_id: int | None = None
    id: str | None = None


@dataclass
class CovariateExtractionResult:
    """Covariate extraction result class definition."""

    covariate_data: list[Covariate]


CovariateExtractStrategy = Callable[
    [
        Iterable[str],
        list[str],
        dict[str, str],
        VerbCallbacks,
        PipelineCache,
        dict[str, Any],
    ],
    Awaitable[CovariateExtractionResult],
]


class ExtractClaimsStrategyType(str, Enum):
    """ExtractClaimsStrategyType class definition."""

    graph_intelligence = "graph_intelligence"

    def __repr__(self):
        """Get a string representation."""
        return f'"{self.value}"'
