# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""LiteLLM completion/embedding cache wrapper."""

import asyncio
from typing import TYPE_CHECKING, Any, Literal

from litellm import EmbeddingResponse, ModelResponse  # type: ignore

from graphrag.language_model.providers.litellm.get_cache_key import get_cache_key
from graphrag.language_model.providers.litellm.types import (
    AsyncLitellmRequestFunc,
    LitellmRequestFunc,
)

if TYPE_CHECKING:
    from graphrag.cache.pipeline_cache import PipelineCache
    from graphrag.config.models.language_model_config import LanguageModelConfig


def with_cache(
    *,
    sync_fn: LitellmRequestFunc,
    async_fn: AsyncLitellmRequestFunc,
    model_config: "LanguageModelConfig",
    cache: "PipelineCache",
    request_type: Literal["chat", "embedding"],
    cache_key_prefix: str,
) -> tuple[LitellmRequestFunc, AsyncLitellmRequestFunc]:
    """
    Wrap the synchronous and asynchronous request functions with caching.

    Args
    ----
        sync_fn: The synchronous chat/embedding request function to wrap.
        async_fn: The asynchronous chat/embedding request function to wrap.
        model_config: The configuration for the language model.
        cache: The cache to use for storing responses.
        request_type: The type of request being made, either "chat" or "embedding".
        cache_key_prefix: The prefix to use for cache keys.

    Returns
    -------
        A tuple containing the wrapped synchronous and asynchronous chat/embedding request functions.
    """

    def _wrapped_with_cache(**kwargs: Any) -> Any:
        is_streaming = kwargs.get("stream", False)
        if is_streaming:
            return sync_fn(**kwargs)
        cache_key = get_cache_key(
            model_config=model_config, prefix=cache_key_prefix, **kwargs
        )
        event_loop = asyncio.get_event_loop()
        cached_response = event_loop.run_until_complete(cache.get(cache_key))
        if (
            cached_response is not None
            and isinstance(cached_response, dict)
            and "response" in cached_response
            and cached_response["response"] is not None
            and isinstance(cached_response["response"], dict)
        ):
            try:
                if request_type == "chat":
                    return ModelResponse(**cached_response["response"])
                return EmbeddingResponse(**cached_response["response"])
            except Exception:  # noqa: BLE001
                # Try to retrieve value from cache but if it fails, continue
                # to make the request.
                ...
        response = sync_fn(**kwargs)
        event_loop.run_until_complete(
            cache.set(cache_key, {"response": response.model_dump()})
        )
        return response

    async def _wrapped_with_cache_async(
        **kwargs: Any,
    ) -> Any:
        is_streaming = kwargs.get("stream", False)
        if is_streaming:
            return await async_fn(**kwargs)
        cache_key = get_cache_key(
            model_config=model_config, prefix=cache_key_prefix, **kwargs
        )
        cached_response = await cache.get(cache_key)
        if (
            cached_response is not None
            and isinstance(cached_response, dict)
            and "response" in cached_response
            and cached_response["response"] is not None
            and isinstance(cached_response["response"], dict)
        ):
            try:
                if request_type == "chat":
                    return ModelResponse(**cached_response["response"])
                return EmbeddingResponse(**cached_response["response"])
            except Exception:  # noqa: BLE001
                # Try to retrieve value from cache but if it fails, continue
                # to make the request.
                ...
        response = await async_fn(**kwargs)
        await cache.set(cache_key, {"response": response.model_dump()})
        return response

    return (_wrapped_with_cache, _wrapped_with_cache_async)
