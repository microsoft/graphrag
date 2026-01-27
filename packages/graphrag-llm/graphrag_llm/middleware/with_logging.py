# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Request count middleware."""

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from graphrag_llm.types import (
        AsyncLLMFunction,
        LLMFunction,
        Metrics,
    )

logger = logging.getLogger(__name__)


def with_logging(
    *,
    sync_middleware: "LLMFunction",
    async_middleware: "AsyncLLMFunction",
) -> tuple[
    "LLMFunction",
    "AsyncLLMFunction",
]:
    """Wrap model functions with logging middleware.

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
        try:
            return sync_middleware(**kwargs)
        except Exception as e:
            retries = metrics.get("retries", None) if metrics else None
            retry_str = f" after {retries} retries" if retries else ""
            logger.exception(
                f"Request failed{retry_str} with exception={e}",  # noqa: G004, TRY401
            )
            raise

    async def _request_count_middleware_async(
        **kwargs: Any,
    ):
        metrics: Metrics | None = kwargs.get("metrics")

        try:
            return await async_middleware(**kwargs)
        except Exception as e:
            retries = metrics.get("retries", None) if metrics else None
            retry_str = f" after {retries} retries" if retries else ""
            logger.exception(
                f"Async request failed{retry_str} with exception={e}",  # noqa: G004, TRY401
            )
            raise

    return (_request_count_middleware, _request_count_middleware_async)  # type: ignore
