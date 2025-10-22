# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Retry middleware."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from graphrag_llm.retry import Retry
    from graphrag_llm.types import (
        AsyncLLMFunction,
        LLMFunction,
    )


def with_retries(
    *,
    sync_middleware: "LLMFunction",
    async_middleware: "AsyncLLMFunction",
    retrier: "Retry",
) -> tuple[
    "LLMFunction",
    "AsyncLLMFunction",
]:
    """Wrap model functions with retry middleware.

    Args
    ----
        sync_middleware: LLMFunction
            The synchronous model function to wrap.
            Either a completion function or an embedding function.
        async_middleware: AsyncLLMFunction
            The asynchronous model function to wrap.
            Either a completion function or an embedding function.
        retrier: Retry
            The retrier instance to use for retrying failed requests.

    Returns
    -------
        tuple[LLMFunction, AsyncLLMFunction]
            The synchronous and asynchronous model functions wrapped with retry middleware.
    """

    def _retry_middleware(
        **kwargs: Any,
    ):
        return retrier.retry(
            func=sync_middleware,
            input_args=kwargs,
        )

    async def _retry_middleware_async(
        **kwargs: Any,
    ):
        return await retrier.retry_async(
            func=async_middleware,
            input_args=kwargs,
        )

    return (_retry_middleware, _retry_middleware_async)  # type: ignore
