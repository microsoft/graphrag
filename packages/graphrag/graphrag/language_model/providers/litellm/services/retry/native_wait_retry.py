# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""LiteLLM Native Retry Service."""

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from graphrag.language_model.providers.litellm.services.retry.retry import Retry

logger = logging.getLogger(__name__)


class NativeRetry(Retry):
    """LiteLLM Native Retry Service."""

    def __init__(
        self,
        *,
        max_retries: int = 5,
        **kwargs: Any,
    ):
        if max_retries <= 0:
            msg = "max_retries must be greater than 0."
            raise ValueError(msg)

        self._max_retries = max_retries

    def retry(self, func: Callable[..., Any], **kwargs: Any) -> Any:
        """Retry a synchronous function."""
        retries = 0
        while True:
            try:
                return func(**kwargs)
            except Exception as e:
                if retries >= self._max_retries:
                    logger.exception(
                        f"NativeRetry: Max retries exceeded, retries={retries}, max_retries={self._max_retries}, exception={e}",  # noqa: G004, TRY401
                    )
                    raise
                retries += 1
                logger.exception(
                    f"NativeRetry: Request failed, immediately retrying, retries={retries}, max_retries={self._max_retries}, exception={e}",  # noqa: G004, TRY401
                )

    async def aretry(
        self,
        func: Callable[..., Awaitable[Any]],
        **kwargs: Any,
    ) -> Any:
        """Retry an asynchronous function."""
        retries = 0
        while True:
            try:
                return await func(**kwargs)
            except Exception as e:
                if retries >= self._max_retries:
                    logger.exception(
                        f"NativeRetry: Max retries exceeded, retries={retries}, max_retries={self._max_retries}, exception={e}",  # noqa: G004, TRY401
                    )
                    raise
                retries += 1
                logger.exception(
                    f"NativeRetry: Request failed, immediately retrying, retries={retries}, max_retries={self._max_retries}, exception={e}",  # noqa: G004, TRY401
                )
