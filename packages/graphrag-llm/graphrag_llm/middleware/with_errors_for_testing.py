# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Error testing middleware."""

import asyncio
import random
import time
from typing import TYPE_CHECKING, Any

import litellm.exceptions as exceptions

if TYPE_CHECKING:
    from graphrag_llm.types import (
        AsyncLLMFunction,
        LLMFunction,
    )


def with_errors_for_testing(
    *,
    sync_middleware: "LLMFunction",
    async_middleware: "AsyncLLMFunction",
    failure_rate: float = 0.0,
    exception_type: str = "ValueError",
    exception_args: list[Any] | None = None,
) -> tuple[
    "LLMFunction",
    "AsyncLLMFunction",
]:
    """Wrap model functions with error testing middleware.

    Args
    ----
        sync_middleware: LLMFunction
            The synchronous model function to wrap.
            Either a completion function or an embedding function.
        async_middleware: AsyncLLMFunction
            The asynchronous model function to wrap.
            Either a completion function or an embedding function.
        failure_rate: float
            The failure rate for testing, between 0.0 and 1.0.
            Defaults to 0.0 (no failures).
        exception_type: str
            The name of the exceptions class from litellm.exceptions to raise.
            Defaults to "ValueError".
        exception_args: list[Any] | None
            The arguments to pass to the exception when raising it. Defaults to None,
            which results in a default message.

    Returns
    -------
        tuple[LLMFunction, AsyncLLMFunction]
            The synchronous and asynchronous model functions wrapped with error testing middleware.
    """

    def _errors_middleware(
        **kwargs: Any,
    ):
        if failure_rate > 0.0 and random.random() <= failure_rate:  # noqa: S311
            time.sleep(0.5)

            exception_cls = exceptions.__dict__.get(exception_type, ValueError)
            raise exception_cls(
                *(exception_args or ["Simulated failure for debugging purposes."])
            )

        return sync_middleware(**kwargs)

    async def _errors_middleware_async(
        **kwargs: Any,
    ):
        if failure_rate > 0.0 and random.random() <= failure_rate:  # noqa: S311
            await asyncio.sleep(0.5)

            exception_cls = exceptions.__dict__.get(exception_type, ValueError)
            raise exception_cls(
                *(exception_args or ["Simulated failure for debugging purposes."])
            )

        return await async_middleware(**kwargs)

    return (_errors_middleware, _errors_middleware_async)  # type: ignore
