# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""LiteLLM completion/embedding retries wrapper."""

from typing import TYPE_CHECKING, Any

from graphrag.language_model.providers.litellm.services.retry.retry_factory import (
    RetryFactory,
)
from graphrag.language_model.providers.litellm.types import (
    AsyncLitellmRequestFunc,
    LitellmRequestFunc,
)

if TYPE_CHECKING:
    from graphrag.config.models.language_model_config import LanguageModelConfig


def with_retries(
    *,
    sync_fn: LitellmRequestFunc,
    async_fn: AsyncLitellmRequestFunc,
    model_config: "LanguageModelConfig",
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
    retry_factory = RetryFactory()
    retry_service = retry_factory.create(
        strategy=model_config.retry_strategy,
        max_retries=model_config.max_retries,
        max_retry_wait=model_config.max_retry_wait,
    )

    def _wrapped_with_retries(**kwargs: Any) -> Any:
        return retry_service.retry(func=sync_fn, **kwargs)

    async def _wrapped_with_retries_async(
        **kwargs: Any,
    ) -> Any:
        return await retry_service.aretry(func=async_fn, **kwargs)

    return (_wrapped_with_retries, _wrapped_with_retries_async)
