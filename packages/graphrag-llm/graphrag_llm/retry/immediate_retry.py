# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Native (immediate) retry implementation."""

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from graphrag_llm.retry.exceptions_to_skip import _default_exceptions_to_skip
from graphrag_llm.retry.retry import Retry

if TYPE_CHECKING:
    from graphrag_llm.types import Metrics


class ImmediateRetry(Retry):
    """Immediate retry implementation."""

    _max_retries: int
    _exceptions_to_skip: list[str]

    def __init__(
        self,
        *,
        max_retries: int = 7,
        exceptions_to_skip: list[str] | None = None,
        **kwargs: dict,
    ) -> None:
        """Initialize ImmediateRetry.

        Args
        ----
            max_retries: int (default=7)
                The maximum number of retries to attempt.

        Raises
        ------
            ValueError
                If max_retries is less than or equal to 0.
        """
        self._max_retries = max_retries
        self._exceptions_to_skip = exceptions_to_skip or _default_exceptions_to_skip

    def retry(self, *, func: Callable[..., Any], input_args: dict[str, Any]) -> Any:
        """Retry a synchronous function."""
        retries: int = 0
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
            finally:
                if metrics is not None:
                    metrics["retries"] = retries
                    metrics["requests_with_retries"] = 1 if retries > 0 else 0
