# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""LiteLLM Exponential Retry Service."""

import asyncio
import logging
import random
import time
from collections.abc import Awaitable, Callable
from typing import Any

from graphrag.language_model.providers.litellm.services.retry.retry import Retry

logger = logging.getLogger(__name__)


class ExponentialRetry(Retry):
    """LiteLLM Exponential Retry Service."""

    def __init__(
        self,
        *,
        max_retries: int = 5,
        base_delay: float = 2.0,
        jitter: bool = True,
        **kwargs: Any,
    ):
        if max_retries <= 0:
            msg = "max_retries must be greater than 0."
            raise ValueError(msg)

        if base_delay <= 1.0:
            msg = "base_delay must be greater than 1.0."
            raise ValueError(msg)

        self._max_retries = max_retries
        self._base_delay = base_delay
        self._jitter = jitter

    def retry(self, func: Callable[..., Any], **kwargs: Any) -> Any:
        """Retry a synchronous function."""
        retries = 0
        delay = 1.0  # Initial delay in seconds
        while True:
            try:
                return func(**kwargs)
            except Exception as e:
                if retries >= self._max_retries:
                    logger.exception(
                        f"ExponentialRetry: Max retries exceeded, retries={retries}, max_retries={self._max_retries}, exception={e}",  # noqa: G004, TRY401
                    )
                    raise
                retries += 1
                delay *= self._base_delay
                logger.exception(
                    f"ExponentialRetry: Request failed, retrying, retries={retries}, delay={delay}, max_retries={self._max_retries}, exception={e}",  # noqa: G004, TRY401
                )
                time.sleep(delay + (self._jitter * random.uniform(0, 1)))  # noqa: S311

    async def aretry(
        self,
        func: Callable[..., Awaitable[Any]],
        **kwargs: Any,
    ) -> Any:
        """Retry an asynchronous function."""
        retries = 0
        delay = 1.0  # Initial delay in seconds
        while True:
            try:
                return await func(**kwargs)
            except Exception as e:
                if retries >= self._max_retries:
                    logger.exception(
                        f"ExponentialRetry: Max retries exceeded, retries={retries}, max_retries={self._max_retries}, exception={e}",  # noqa: G004, TRY401
                    )
                    raise
                retries += 1
                delay *= self._base_delay
                logger.exception(
                    f"ExponentialRetry: Request failed, retrying, retries={retries}, delay={delay}, max_retries={self._max_retries}, exception={e}",  # noqa: G004, TRY401
                )
                await asyncio.sleep(delay + (self._jitter * random.uniform(0, 1)))  # noqa: S311
