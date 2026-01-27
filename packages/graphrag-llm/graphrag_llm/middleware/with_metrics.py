# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Metrics middleware to process metrics using a MetricsProcessor."""

import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from graphrag_llm.config import ModelConfig
    from graphrag_llm.metrics import MetricsProcessor
    from graphrag_llm.types import (
        AsyncLLMFunction,
        LLMFunction,
        Metrics,
    )


def with_metrics(
    *,
    model_config: "ModelConfig",
    sync_middleware: "LLMFunction",
    async_middleware: "AsyncLLMFunction",
    metrics_processor: "MetricsProcessor",
) -> tuple[
    "LLMFunction",
    "AsyncLLMFunction",
]:
    """Wrap model functions with metrics middleware.

    Args
    ----
        model_config: ModelConfig
            The model configuration.
        sync_middleware: LLMFunction
            The synchronous model function to wrap.
            Either a completion function or an embedding function.
        async_middleware: AsyncLLMFunction
            The asynchronous model function to wrap.
            Either a completion function or an embedding function.
        metrics_processor: MetricsProcessor
            The metrics processor to use.

    Returns
    -------
        tuple[LLMFunction, AsyncLLMFunction]
            The synchronous and asynchronous model functions wrapped with metrics middleware.

    """

    def _metrics_middleware(
        **kwargs: Any,
    ):
        metrics: Metrics | None = kwargs.get("metrics")
        start_time = time.time()
        response = sync_middleware(**kwargs)
        end_time = time.time()

        if metrics is not None:
            metrics_processor.process_metrics(
                model_config=model_config,
                metrics=metrics,
                input_args=kwargs,
                response=response,
            )
            if kwargs.get("stream"):
                metrics["compute_duration_seconds"] = 0
                metrics["streaming_responses"] = 1
            else:
                metrics["compute_duration_seconds"] = end_time - start_time
                metrics["streaming_responses"] = 0
        return response

    async def _metrics_middleware_async(
        **kwargs: Any,
    ):
        metrics: Metrics | None = kwargs.get("metrics")

        start_time = time.time()
        response = await async_middleware(**kwargs)
        end_time = time.time()

        if metrics is not None:
            metrics_processor.process_metrics(
                model_config=model_config,
                metrics=metrics,
                input_args=kwargs,
                response=response,
            )
            if kwargs.get("stream"):
                metrics["compute_duration_seconds"] = 0
                metrics["streaming_responses"] = 1
            else:
                metrics["compute_duration_seconds"] = end_time - start_time
                metrics["streaming_responses"] = 0
        return response

    return (_metrics_middleware, _metrics_middleware_async)  # type: ignore
