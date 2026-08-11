# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Unit tests for the LLM cache middleware."""

import asyncio
from collections.abc import Callable
from typing import Any

import pytest
from graphrag_cache.memory_cache import MemoryCache
from graphrag_llm.middleware.with_cache import with_cache
from graphrag_llm.types import LLMCompletionResponse
from graphrag_llm.utils import create_completion_response


@pytest.fixture
def tracked_event_loops(monkeypatch: pytest.MonkeyPatch):
    """Install a caller-owned loop and track loops created by the middleware."""
    original_loop = asyncio.new_event_loop()
    create_event_loop = asyncio.new_event_loop
    created_loops: list[asyncio.AbstractEventLoop] = []

    def _create_event_loop() -> asyncio.AbstractEventLoop:
        event_loop = create_event_loop()
        created_loops.append(event_loop)
        return event_loop

    asyncio.set_event_loop(original_loop)
    monkeypatch.setattr(asyncio, "new_event_loop", _create_event_loop)

    yield original_loop, created_loops

    asyncio.set_event_loop(None)
    original_loop.close()
    for event_loop in created_loops:
        if not event_loop.is_closed():
            event_loop.close()


def _with_sync_cache(
    cache: MemoryCache,
    sync_middleware: Callable[..., LLMCompletionResponse],
):
    async def _async_middleware(**kwargs: Any) -> LLMCompletionResponse:
        return await asyncio.to_thread(sync_middleware, **kwargs)

    def _cache_key(input_args: dict[str, Any]) -> str:
        return "cache-key"

    cached_middleware, _ = with_cache(
        sync_middleware=sync_middleware,
        async_middleware=_async_middleware,
        request_type="chat",
        cache=cache,
        cache_key_creator=_cache_key,
    )
    return cached_middleware


def test_sync_cache_preserves_event_loop_on_miss(tracked_event_loops) -> None:
    """The sync cache should not replace the caller's loop on a cache miss."""
    original_loop, created_loops = tracked_event_loops
    response = create_completion_response("uncached")
    cached_middleware = _with_sync_cache(MemoryCache(), lambda **_: response)

    cached_response = cached_middleware(messages=[])

    assert isinstance(cached_response, LLMCompletionResponse)
    assert cached_response.content == "uncached"
    assert asyncio.get_event_loop() is original_loop
    assert len(created_loops) == 1
    assert created_loops[0].is_closed()


def test_sync_cache_preserves_event_loop_on_hit(tracked_event_loops) -> None:
    """The sync cache should close its loop before returning a cached response."""
    original_loop, created_loops = tracked_event_loops
    response = create_completion_response("cached")
    cache = MemoryCache()
    asyncio.run(
        cache.set(
            "cache-key",
            {"response": response.model_dump(), "metrics": {}},
        )
    )
    asyncio.set_event_loop(original_loop)

    def _unexpected_request(**_: Any) -> LLMCompletionResponse:
        pytest.fail("The wrapped middleware should not run on a cache hit.")

    cached_middleware = _with_sync_cache(cache, _unexpected_request)

    cached_response = cached_middleware(messages=[])

    assert isinstance(cached_response, LLMCompletionResponse)
    assert cached_response.content == "cached"
    assert asyncio.get_event_loop() is original_loop
    assert len(created_loops) == 1
    assert created_loops[0].is_closed()


def test_sync_cache_closes_event_loop_on_error(tracked_event_loops) -> None:
    """The sync cache should close its loop when the wrapped middleware fails."""
    original_loop, created_loops = tracked_event_loops

    def _raise_error(**_: Any) -> LLMCompletionResponse:
        msg = "request failed"
        raise RuntimeError(msg)

    cached_middleware = _with_sync_cache(MemoryCache(), _raise_error)

    with pytest.raises(RuntimeError, match="request failed"):
        cached_middleware(messages=[])

    assert asyncio.get_event_loop() is original_loop
    assert len(created_loops) == 1
    assert created_loops[0].is_closed()
