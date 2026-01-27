# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Default Metrics Processor."""

from typing import TYPE_CHECKING, Any

from graphrag_llm.metrics.metrics_processor import MetricsProcessor
from graphrag_llm.model_cost_registry import model_cost_registry
from graphrag_llm.types import LLMCompletionResponse, LLMEmbeddingResponse

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

    from graphrag_llm.config import ModelConfig
    from graphrag_llm.types import (
        LLMCompletionChunk,
        Metrics,
    )


class DefaultMetricsProcessor(MetricsProcessor):
    """Default metrics processor that does nothing."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize DefaultMetricsProcessor."""

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
        """Process metrics."""
        self._process_metrics_common(
            model_config=model_config,
            metrics=metrics,
            input_args=input_args,
            response=response,
        )

    def _process_metrics_common(
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
        if isinstance(response, LLMCompletionResponse):
            self._process_lm_chat_completion(
                model_config=model_config,
                metrics=metrics,
                input_args=input_args,
                response=response,
            )
        elif isinstance(response, LLMEmbeddingResponse):
            self._process_lm_embedding_response(
                model_config=model_config,
                metrics=metrics,
                input_args=input_args,
                response=response,
            )

    def _process_lm_chat_completion(
        self,
        model_config: "ModelConfig",
        metrics: "Metrics",
        input_args: dict[str, Any],
        response: "LLMCompletionResponse",
    ) -> None:
        """Process LMChatCompletion metrics."""
        prompt_tokens = response.usage.prompt_tokens if response.usage else 0
        completion_tokens = response.usage.completion_tokens if response.usage else 0
        total_tokens = prompt_tokens + completion_tokens

        if total_tokens > 0:
            metrics["responses_with_tokens"] = 1
            metrics["prompt_tokens"] = prompt_tokens
            metrics["completion_tokens"] = completion_tokens
            metrics["total_tokens"] = total_tokens

            model_id = f"{model_config.model_provider}/{model_config.model}"
            model_costs = model_cost_registry.get_model_costs(model_id)

            if not model_costs:
                return

            input_cost = prompt_tokens * model_costs["input_cost_per_token"]
            output_cost = completion_tokens * model_costs["output_cost_per_token"]
            total_cost = input_cost + output_cost

            metrics["responses_with_cost"] = 1
            metrics["input_cost"] = input_cost
            metrics["output_cost"] = output_cost
            metrics["total_cost"] = total_cost

    def _process_lm_embedding_response(
        self,
        model_config: "ModelConfig",
        metrics: "Metrics",
        input_args: dict[str, Any],
        response: "LLMEmbeddingResponse",
    ) -> None:
        """Process LLMEmbeddingResponse metrics."""
        prompt_tokens = response.usage.prompt_tokens if response.usage else 0

        if prompt_tokens > 0:
            metrics["responses_with_tokens"] = 1
            metrics["prompt_tokens"] = prompt_tokens
            metrics["total_tokens"] = prompt_tokens

            model_id = f"{model_config.model_provider}/{model_config.model}"
            model_costs = model_cost_registry.get_model_costs(model_id)

            if not model_costs:
                return

            input_cost = prompt_tokens * model_costs["input_cost_per_token"]
            metrics["responses_with_cost"] = 1
            metrics["input_cost"] = input_cost
            metrics["total_cost"] = input_cost
