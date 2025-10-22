# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Request count middleware."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from graphrag_llm.types import (
        AsyncLLMFunction,
        LLMFunction,
        Metrics,
    )


def with_request_count(
    *,
    sync_middleware: "LLMFunction",
    async_middleware: "AsyncLLMFunction",
) -> tuple[
    "LLMFunction",
    "AsyncLLMFunction",
]:
    """Wrap model functions with request count middleware.

    This is the first step in the middleware pipeline.
    It counts how many requests were made, how many succeeded, and how many failed

    Args
    ----
        sync_middleware: LLMFunction
            The synchronous model function to wrap.
            Either a completion function or an embedding function.
        async_middleware: AsyncLLMFunction
            The asynchronous model function to wrap.
            Either a completion function or an embedding function.

    Returns
    -------
        tuple[LLMFunction, AsyncLLMFunction]
            The synchronous and asynchronous model functions wrapped with request count middleware.
    """

    def _request_count_middleware(
        **kwargs: Any,
    ):
        metrics: Metrics | None = kwargs.get("metrics")
        if metrics is not None:
            metrics["attempted_request_count"] = 1
            metrics["successful_response_count"] = 0
            metrics["failed_response_count"] = 0
        try:
            result = sync_middleware(**kwargs)
            if metrics is not None:
                metrics["successful_response_count"] = 1
            return result  # noqa: TRY300
        except Exception:
            if metrics is not None:
                metrics["failed_response_count"] = 1
            raise

    async def _request_count_middleware_async(
        **kwargs: Any,
    ):
        metrics: Metrics | None = kwargs.get("metrics")

        if metrics is not None:
            metrics["attempted_request_count"] = 1
            metrics["successful_response_count"] = 0
            metrics["failed_response_count"] = 0
        try:
            result = await async_middleware(**kwargs)
            if metrics is not None:
                metrics["successful_response_count"] = 1
            return result  # noqa: TRY300
        except Exception:
            if metrics is not None:
                metrics["failed_response_count"] = 1
            raise

    return (_request_count_middleware, _request_count_middleware_async)  # type: ignore
