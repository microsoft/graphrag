# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Exponential backoff retry implementation."""

import asyncio
import random
import time
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from graphrag_llm.retry.exceptions_to_skip import _default_exceptions_to_skip
from graphrag_llm.retry.retry import Retry

if TYPE_CHECKING:
    from graphrag_llm.types import Metrics


class ExponentialRetry(Retry):
    """Exponential backoff retry implementation."""

    _base_delay: float
    _jitter: bool
    _max_retries: int
    _max_delay: float
    _exceptions_to_skip: list[str]

    def __init__(
        self,
        *,
        max_retries: int = 7,  # 2^7 = 128 second max delay with default settings
        base_delay: float = 2.0,
        jitter: bool = True,
        max_delay: float | None = None,
        exceptions_to_skip: list[str] | None = None,
        **kwargs: dict,
    ) -> None:
        """Initialize ExponentialRetry.

        Args
        ----
            max_retries: int (default=7, 2^7 = 128 second max delay with default settings)
                The maximum number of retries to attempt.
            base_delay: float
                The base delay multiplier for exponential backoff.
            jitter: bool
                Whether to apply jitter to the delay intervals.
            max_delay: float | None
                The maximum delay between retries. If None, there is no limit.

        Raises
        ------
            ValueError
                If max_retries is less than or equal to 0.
                If base_delay is less than or equal to 1.0.
        """
        self._base_delay = base_delay
        self._jitter = jitter
        self._max_retries = max_retries
        self._max_delay = max_delay or float("inf")
        self._exceptions_to_skip = exceptions_to_skip or _default_exceptions_to_skip

    def retry(self, *, func: Callable[..., Any], input_args: dict[str, Any]) -> Any:
        """Retry a synchronous function."""
        retries: int = 0
        delay = 1.0
        metrics: Metrics | None = input_args.get("metrics")
        while True:
            try:
                return func(**input_args)
            except Exception as e:
                if e.__class__.__name__ in self._exceptions_to_skip:
                    raise

                if retries >= self._max_retries:
                    raise
                retries += 1
                delay *= self._base_delay
                sleep_delay = min(
                    self._max_delay,
                    delay + (self._jitter * random.uniform(0, 1)),  # noqa: S311
                )

                time.sleep(sleep_delay)
            finally:
                if metrics is not None:
                    metrics["retries"] = retries
                    metrics["requests_with_retries"] = 1 if retries > 0 else 0

    async def retry_async(
        self,
        *,
        func: Callable[..., Awaitable[Any]],
        input_args: dict[str, Any],
    ) -> Any:
        """Retry an asynchronous function."""
        retries: int = 0
        delay = 1.0
        metrics: Metrics | None = input_args.get("metrics")
        while True:
            try:
                return await func(**input_args)
            except Exception as e:
                if e.__class__.__name__ in self._exceptions_to_skip:
                    raise
                if retries >= self._max_retries:
                    raise
                retries += 1
                delay *= self._base_delay
                sleep_delay = min(
                    self._max_delay,
                    delay + (self._jitter * random.uniform(0, 1)),  # noqa: S311
                )

                await asyncio.sleep(sleep_delay)
            finally:
                if metrics is not None:
                    metrics["retries"] = retries
                    metrics["requests_with_retries"] = 1 if retries > 0 else 0
