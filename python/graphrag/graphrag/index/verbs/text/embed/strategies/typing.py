#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""A module containing 'TextEmbeddingResult' model."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from datashaper import VerbCallbacks

from graphrag.index.cache import PipelineCache


@dataclass
class TextEmbeddingResult:
    """Text embedding result class definition."""

    embeddings: list[list[float] | None] | None


TextEmbeddingStrategy = Callable[
    [
        list[str],
        VerbCallbacks,
        PipelineCache,
        dict,
    ],
    Awaitable[TextEmbeddingResult],
]
