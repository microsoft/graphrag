# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""LiteLLM Incremental Wait Retry Service."""

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

from graphrag.language_model.providers.litellm.services.retry.retry import Retry

logger = logging.getLogger(__name__)


class IncrementalWaitRetry(Retry):
    """LiteLLM Incremental Wait Retry Service."""

    def __init__(
        self,
        *,
        max_retry_wait: float,
        max_retries: int = 5,
        **kwargs: Any,
    ):
        if max_retries <= 0:
            msg = "max_retries must be greater than 0."
            raise ValueError(msg)

        if max_retry_wait <= 0:
            msg = "max_retry_wait must be greater than 0."
            raise ValueError(msg)

        self._max_retries = max_retries
        self._max_retry_wait = max_retry_wait
        self._increment = max_retry_wait / max_retries

    def retry(self, func: Callable[..., Any], **kwargs: Any) -> Any:
        """Retry a synchronous function."""
        retries = 0
        delay = 0.0
        while True:
            try:
                return func(**kwargs)
            except Exception as e:
                if retries >= self._max_retries:
                    logger.exception(
                        f"IncrementalWaitRetry: Max retries exceeded, retries={retries}, max_retries={self._max_retries}, exception={e}",  # noqa: G004, TRY401
                    )
                    raise
                retries += 1
                delay += self._increment
                logger.exception(
                    f"IncrementalWaitRetry: Request failed, retrying after incremental delay, retries={retries}, delay={delay}, max_retries={self._max_retries}, exception={e}",  # noqa: G004, TRY401
                )
                time.sleep(delay)

    async def aretry(
        self,
        func: Callable[..., Awaitable[Any]],
        **kwargs: Any,
    ) -> Any:
        """Retry an asynchronous function."""
        retries = 0
        delay = 0.0
        while True:
            try:
                return await func(**kwargs)
            except Exception as e:
                if retries >= self._max_retries:
                    logger.exception(
                        f"IncrementalWaitRetry: Max retries exceeded, retries={retries}, max_retries={self._max_retries}, exception={e}",  # noqa: G004, TRY401
                    )
                    raise
                retries += 1
                delay += self._increment
                logger.exception(
                    f"IncrementalWaitRetry: Request failed, retrying after incremental delay, retries={retries}, delay={delay}, max_retries={self._max_retries}, exception={e}",  # noqa: G004, TRY401
                )
                await asyncio.sleep(delay)
