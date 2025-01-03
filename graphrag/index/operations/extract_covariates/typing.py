# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'Covariate' and 'CovariateExtractionResult' models."""

from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass
from typing import Any

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks


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
        WorkflowCallbacks,
        PipelineCache,
        dict[str, Any],
    ],
    Awaitable[CovariateExtractionResult],
]
