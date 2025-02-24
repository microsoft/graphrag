# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""FNLLM Cache provider."""

from typing import Any

from fnllm.caching import Cache as FNLLMCache

from graphrag.cache.pipeline_cache import PipelineCache


class FNLLMCacheProvider(FNLLMCache):
    """A cache for the pipeline."""

    def __init__(self, cache: PipelineCache):
        self._cache = cache

    async def has(self, key: str) -> bool:
        """Check if the cache has a value."""
        return await self._cache.has(key)

    async def get(self, key: str) -> Any | None:
        """Retrieve a value from the cache."""
        return await self._cache.get(key)

    async def set(
        self, key: str, value: Any, metadata: dict[str, Any] | None = None
    ) -> None:
        """Write a value into the cache."""
        await self._cache.set(key, value, metadata)

    async def remove(self, key: str) -> None:
        """Remove a value from the cache."""
        await self._cache.delete(key)

    async def clear(self) -> None:
        """Clear the cache."""
        await self._cache.clear()

    def child(self, key: str) -> "FNLLMCacheProvider":
        """Create a child cache."""
        child_cache = self._cache.child(key)
        return FNLLMCacheProvider(child_cache)
