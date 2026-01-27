# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'Finding' and 'CommunityReport' models."""

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from typing_extensions import TypedDict

if TYPE_CHECKING:
    from graphrag_llm.completion import LLMCompletion

RowContext = dict[str, Any]
Claim = dict[str, Any]


class Finding(TypedDict):
    """Finding class definition."""

    summary: str
    explanation: str


class CommunityReport(TypedDict):
    """Community report class definition."""

    community: str | int
    title: str
    summary: str
    full_content: str
    full_content_json: str
    rank: float
    level: int
    rating_explanation: str
    findings: list[Finding]


CommunityReportsStrategy = Callable[
    [
        str | int,
        str,
        int,
        "LLMCompletion",
        str,
        int,
    ],
    Awaitable[CommunityReport | None],
]
