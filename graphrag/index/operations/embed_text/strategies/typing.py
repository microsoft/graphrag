# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'TextEmbeddingResult' model."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.callbacks.verb_callbacks import VerbCallbacks


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
