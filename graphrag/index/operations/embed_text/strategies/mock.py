# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run and _embed_text methods definitions."""

import random
from collections.abc import Iterable
from typing import Any

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.index.operations.embed_text.strategies.typing import TextEmbeddingResult
from graphrag.logger.progress import ProgressTicker, progress_ticker


async def run(  # noqa RUF029 async is required for interface
    input: list[str],
    callbacks: WorkflowCallbacks,
    cache: PipelineCache,
    _args: dict[str, Any],
) -> TextEmbeddingResult:
    """Run the Claim extraction chain."""
    input = input if isinstance(input, Iterable) else [input]
    ticker = progress_ticker(callbacks.progress, len(input))
    return TextEmbeddingResult(
        embeddings=[_embed_text(cache, text, ticker) for text in input]
    )


def _embed_text(_cache: PipelineCache, _text: str, tick: ProgressTicker) -> list[float]:
    """Embed a single piece of text."""
    tick(1)
    return [random.random(), random.random(), random.random()]  # noqa S311
