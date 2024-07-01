# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'TextTranslationResult' model."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from datashaper import VerbCallbacks

from graphrag.index.cache import PipelineCache


@dataclass
class TextTranslationResult:
    """Text translation result class definition."""

    translations: list[str]


TextTranslationStrategy = Callable[
    [list[str], dict[str, Any], VerbCallbacks, PipelineCache],
    Awaitable[TextTranslationResult],
]
