# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Metrics processor abstract base class."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

    from graphrag_llm.config import ModelConfig
    from graphrag_llm.types import (
        LLMCompletionChunk,
        LLMCompletionResponse,
        LLMEmbeddingResponse,
        Metrics,
    )


class MetricsProcessor(ABC):
    """Abstract base class for metrics processors."""

    @abstractmethod
    def __init__(self, **kwargs: Any):
        """Initialize MetricsProcessor."""
        raise NotImplementedError

    @abstractmethod
    def process_metrics(
        self,
        *,
        model_config: "ModelConfig",
        metrics: "Metrics",
        input_args: dict[str, Any],
        response: "LLMCompletionResponse \
            | Iterator[LLMCompletionChunk] \
            | AsyncIterator[LLMCompletionChunk] \
            | LLMEmbeddingResponse",
    ) -> None:
        """Process metrics.

        Update the metrics dictionary in place.

        Args
        ----
            metrics: Metrics
                The metrics to process.
            input_args: dict[str, Any]
                The input arguments passed to completion or embedding
                used to generate the response.
            response: LLMCompletionResponse | Iterator[LLMCompletionChunk] | LLMEmbeddingResponse
                Either a completion or embedding response from the LLM.

        Returns
        -------
            None
        """
        raise NotImplementedError
