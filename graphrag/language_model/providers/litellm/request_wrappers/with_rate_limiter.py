# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""LiteLLM completion/embedding rate limiter wrapper."""

from typing import TYPE_CHECKING, Any

from litellm import token_counter  # type: ignore

from graphrag.language_model.providers.litellm.services.rate_limiter.rate_limiter_factory import (
    RateLimiterFactory,
)
from graphrag.language_model.providers.litellm.types import (
    AsyncLitellmRequestFunc,
    LitellmRequestFunc,
)

if TYPE_CHECKING:
    from graphrag.config.models.language_model_config import LanguageModelConfig


def with_rate_limiter(
    *,
    sync_fn: LitellmRequestFunc,
    async_fn: AsyncLitellmRequestFunc,
    model_config: "LanguageModelConfig",
    rpm: int | None = None,
    tpm: int | None = None,
) -> tuple[LitellmRequestFunc, AsyncLitellmRequestFunc]:
    """
    Wrap the synchronous and asynchronous request functions with rate limiting.

    Args
    ----
        sync_fn: The synchronous chat/embedding request function to wrap.
        async_fn: The asynchronous chat/embedding request function to wrap.
        model_config: The configuration for the language model.
        processing_event: A threading event that can be used to pause the rate limiter.
        rpm: An optional requests per minute limit.
        tpm: An optional tokens per minute limit.

    If `rpm` and `tpm` is set to 0 or None, rate limiting is disabled.

    Returns
    -------
        A tuple containing the wrapped synchronous and asynchronous chat/embedding request functions.
    """
    rate_limiter_factory = RateLimiterFactory()

    if (
        model_config.rate_limit_strategy is None
        or model_config.rate_limit_strategy not in rate_limiter_factory
    ):
        msg = f"Rate Limiter strategy '{model_config.rate_limit_strategy}' is none or not registered. Available strategies: {', '.join(rate_limiter_factory.keys())}"
        raise ValueError(msg)

    rate_limiter_service = rate_limiter_factory.create(
        strategy=model_config.rate_limit_strategy, rpm=rpm, tpm=tpm
    )

    max_tokens = model_config.max_completion_tokens or model_config.max_tokens or 0

    def _wrapped_with_rate_limiter(**kwargs: Any) -> Any:
        token_count = max_tokens
        if "messages" in kwargs:
            token_count += token_counter(
                model=model_config.model,
                messages=kwargs["messages"],
            )
        elif "input" in kwargs:
            token_count += token_counter(
                model=model_config.model,
                text=kwargs["input"],
            )

        with rate_limiter_service.acquire(token_count=token_count):
            return sync_fn(**kwargs)

    async def _wrapped_with_rate_limiter_async(
        **kwargs: Any,
    ) -> Any:
        token_count = max_tokens
        if "messages" in kwargs:
            token_count += token_counter(
                model=model_config.model,
                messages=kwargs["messages"],
            )
        elif "input" in kwargs:
            token_count += token_counter(
                model=model_config.model,
                text=kwargs["input"],
            )

        with rate_limiter_service.acquire(token_count=token_count):
            return await async_fn(**kwargs)

    return (_wrapped_with_rate_limiter, _wrapped_with_rate_limiter_async)
