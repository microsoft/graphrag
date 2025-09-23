# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""LiteLLM completion/embedding logging wrapper."""

import logging
from typing import Any

from graphrag.language_model.providers.litellm.types import (
    AsyncLitellmRequestFunc,
    LitellmRequestFunc,
)

logger = logging.getLogger(__name__)


def with_logging(
    *,
    sync_fn: LitellmRequestFunc,
    async_fn: AsyncLitellmRequestFunc,
) -> tuple[LitellmRequestFunc, AsyncLitellmRequestFunc]:
    """
    Wrap the synchronous and asynchronous request functions with retries.

    Args
    ----
        sync_fn: The synchronous chat/embedding request function to wrap.
        async_fn: The asynchronous chat/embedding request function to wrap.
        model_config: The configuration for the language model.

    Returns
    -------
        A tuple containing the wrapped synchronous and asynchronous chat/embedding request functions.
    """

    def _wrapped_with_logging(**kwargs: Any) -> Any:
        try:
            return sync_fn(**kwargs)
        except Exception as e:
            logger.exception(
                f"with_logging: Request failed with exception={e}",  # noqa: G004, TRY401
            )
            raise

    async def _wrapped_with_logging_async(
        **kwargs: Any,
    ) -> Any:
        try:
            return await async_fn(**kwargs)
        except Exception as e:
            logger.exception(
                f"with_logging: Async request failed with exception={e}",  # noqa: G004, TRY401
            )
            raise

    return (_wrapped_with_logging, _wrapped_with_logging_async)
