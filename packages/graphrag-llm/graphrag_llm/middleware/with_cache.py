# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Cache middleware."""

import asyncio
from typing import TYPE_CHECKING, Any, Literal

from graphrag_llm.types import LLMCompletionResponse, LLMEmbeddingResponse

if TYPE_CHECKING:
    from graphrag_cache import Cache, CacheKeyCreator

    from graphrag_llm.types import (
        AsyncLLMFunction,
        LLMFunction,
        Metrics,
    )


def with_cache(
    *,
    sync_middleware: "LLMFunction",
    async_middleware: "AsyncLLMFunction",
    request_type: Literal["chat", "embedding"],
    cache: "Cache",
    cache_key_creator: "CacheKeyCreator",
) -> tuple[
    "LLMFunction",
    "AsyncLLMFunction",
]:
    """Wrap model functions with cache middleware.

    Args
    ----
        sync_middleware: LLMFunction
            The synchronous model function to wrap.
            Either a completion function or an embedding function.
        async_middleware: AsyncLLMFunction
            The asynchronous model function to wrap.
            Either a completion function or an embedding function.
        cache: Cache
            The cache instance to use.
        request_type: Literal["chat", "embedding"]
            The type of request, either "chat" or "embedding".
        cache_key_creator: CacheKeyCreator
            The cache key creator to use.

    Returns
    -------
        tuple[LLMFunction, AsyncLLMFunction]
            The synchronous and asynchronous model functions with caching.

    """

    def _cache_middleware(
        **kwargs: Any,
    ):
        is_streaming = kwargs.get("stream") or False
        is_mocked = kwargs.get("mock_response") or False
        metrics: Metrics | None = kwargs.get("metrics")

        if is_streaming or is_mocked:
            # don't cache streaming or mocked responses
            return sync_middleware(**kwargs)

        cache_key = cache_key_creator(kwargs)

        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        cached_response = event_loop.run_until_complete(cache.get(cache_key))
        if (
            cached_response is not None
            and isinstance(cached_response, dict)
            and "response" in cached_response
            and cached_response["response"] is not None
            and isinstance(cached_response["response"], dict)
        ):
            try:
                if (
                    metrics is not None
                    and "metrics" in cached_response
                    and cached_response["metrics"] is not None
                    and isinstance(cached_response["metrics"], dict)
                ):
                    metrics.update(cached_response["metrics"])
                    metrics["cached_responses"] = 1

                if request_type == "chat":
                    return LLMCompletionResponse(**cached_response["response"])
                return LLMEmbeddingResponse(**cached_response["response"])
            except Exception:  # noqa: BLE001
                # Try to retrieve value from cache but if it fails, continue
                # to make the request.
                ...

        response = sync_middleware(**kwargs)
        cache_value = {
            "response": response.model_dump(),  # type: ignore
            "metrics": metrics if metrics is not None else {},
        }
        event_loop.run_until_complete(cache.set(cache_key, cache_value))
        event_loop.close()
        return response

    async def _cache_middleware_async(
        **kwargs: Any,
    ):
        is_streaming = kwargs.get("stream") or False
        is_mocked = kwargs.get("mock_response") or False
        metrics: Metrics | None = kwargs.get("metrics")

        if is_streaming or is_mocked:
            # don't cache streaming or mocked responses
            return await async_middleware(**kwargs)

        cache_key = cache_key_creator(kwargs)

        cached_response = await cache.get(cache_key)
        if (
            cached_response is not None
            and isinstance(cached_response, dict)
            and "response" in cached_response
            and cached_response["response"] is not None
            and isinstance(cached_response["response"], dict)
        ):
            try:
                if (
                    metrics is not None
                    and "metrics" in cached_response
                    and cached_response["metrics"] is not None
                    and isinstance(cached_response["metrics"], dict)
                ):
                    metrics.update(cached_response["metrics"])
                    metrics["cached_responses"] = 1

                if request_type == "chat":
                    return LLMCompletionResponse(**cached_response["response"])
                return LLMEmbeddingResponse(**cached_response["response"])
            except Exception:  # noqa: BLE001
                # Try to retrieve value from cache but if it fails, continue
                # to make the request.
                ...

        response = await async_middleware(**kwargs)
        cache_value = {
            "response": response.model_dump(),  # type: ignore
            "metrics": metrics if metrics is not None else {},
        }
        await cache.set(cache_key, cache_value)
        return response

    return (_cache_middleware, _cache_middleware_async)  # type: ignore
