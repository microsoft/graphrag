# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'SummarizedDescriptionResult' model."""

from dataclasses import dataclass
from typing import Any, NamedTuple


@dataclass
class SummarizedDescriptionResult:
    """Entity summarization result class definition."""

    id: str | tuple[str, str]
    description: str


class DescriptionSummarizeRow(NamedTuple):
    """DescriptionSummarizeRow class definition."""

    graph: Any
