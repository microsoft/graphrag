# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""LiteLLM Retry Abstract Base Class."""

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any


class Retry(ABC):
    """LiteLLM Retry Abstract Base Class.

    Added lightweight pipeline context support to allow retry implementations
    to record retry counts.
    """

    def __init__(self, /, **kwargs: Any):
        self._pipeline_context: Any | None = None

    def set_pipeline_context(self, context: Any) -> None:
        """Inject pipeline context (optional).

        The context is expected to expose a `record_llm_retries(int)` method. If it does not, retry tracking
        is silently skipped.
        """
        self._pipeline_context = context

    def _record_retries(self, retry_count: int) -> None:
        """Record retry attempts to pipeline context (if available).

        This is a protected method intended for use by subclasses in their
        finally blocks to ensure retry counts are recorded regardless of
        success or failure.

        Args
        ----
            retry_count: Number of retry attempts performed.

        """
        if self._pipeline_context is not None and retry_count > 0:
            try:
                self._pipeline_context.record_llm_retries(retry_count)
            except AttributeError:
                # Context doesn't support retry tracking, skip silently
                pass

    @abstractmethod
    def retry(self, func: Callable[..., Any], **kwargs: Any) -> Any:
        """Retry a synchronous function."""
        msg = "Subclasses must implement this method"
        raise NotImplementedError(msg)

    @abstractmethod
    async def aretry(
        self,
        func: Callable[..., Awaitable[Any]],
        **kwargs: Any,
    ) -> Any:
        """Retry an asynchronous function."""
        msg = "Subclasses must implement this method"
        raise NotImplementedError(msg)
