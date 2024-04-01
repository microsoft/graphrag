#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

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
