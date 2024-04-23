# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""A module containing 'Finding' and 'CommunityReport' models."""

from collections.abc import Awaitable, Callable
from typing import Any

from datashaper import VerbCallbacks
from pydantic.dataclasses import dataclass

from graphrag.index.cache import PipelineCache

ExtractedEntity = dict[str, Any]
StrategyConfig = dict[str, Any]
RowContext = dict[str, Any]
EntityTypes = list[str]
Claim = dict[str, Any]


@dataclass
class Finding:
    """Finding class definition."""

    summary: str
    explanation: str


@dataclass
class CommunityReport:
    """Community report class definition."""

    community: str | int
    title: str
    summary: str
    full_content: str
    full_content_json: str
    rank: float | None
    level: str | int | None
    rank_explanation: str | None
    findings: list[Finding]


CommunityReportsStrategy = Callable[
    [
        str | int,
        str,
        str | int,
        VerbCallbacks,
        PipelineCache,
        StrategyConfig,
    ],
    Awaitable[CommunityReport | None],
]
