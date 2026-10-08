# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Shared tests for bulk cache reads."""

from typing import Any

import pytest
from graphrag_cache.cache import Cache
from graphrag_cache.json_cache import JsonCache
from graphrag_cache.memory_cache import MemoryCache
from graphrag_cache.noop_cache import NoopCache
from graphrag_cache.sqlite_cache import SQLiteCache
from graphrag_storage.file_storage import FileStorage
from graphrag_storage.memory_storage import MemoryStorage


@pytest.fixture(params=["json", "memory", "noop", "sqlite"])
def cache(request, tmp_path) -> Cache:
    """Create each built-in cache backend."""
    if request.param == "json":
        return JsonCache(storage=MemoryStorage())
    if request.param == "memory":
        return MemoryCache()
    if request.param == "noop":
        return NoopCache()
    return SQLiteCache(FileStorage(base_dir=str(tmp_path)))


@pytest.mark.asyncio
async def test_get_many_empty_input_returns_empty(cache):
    assert await cache.get_many([]) == {}


@pytest.mark.asyncio
async def test_get_many_returns_hits_and_omits_misses(cache):
    await cache.set("first", {"value": 1})
    await cache.set("second", ["two"])

    expected = (
        {}
        if isinstance(cache, NoopCache)
        else {"first": {"value": 1}, "second": ["two"]}
    )

    assert await cache.get_many(["first", "missing", "second"]) == expected


@pytest.mark.asyncio
async def test_get_many_deduplicates_keys_and_matches_get(cache):
    await cache.set("key", {"nested": [1, 2, 3]})

    result = await cache.get_many(["key", "key"])
    value = await cache.get("key")

    assert result == ({} if value is None else {"key": value})


@pytest.mark.asyncio
async def test_get_many_child_namespaces_are_isolated(cache):
    child = cache.child("child")
    await cache.set("key", "root")
    await child.set("key", "child")

    root_value = await cache.get("key")
    child_value = await child.get("key")

    assert await cache.get_many(["key"]) == (
        {} if root_value is None else {"key": root_value}
    )
    assert await child.get_many(["key"]) == (
        {} if child_value is None else {"key": child_value}
    )


@pytest.mark.asyncio
async def test_default_get_many_supports_custom_cache_implementations():
    class CustomCache(Cache):
        def __init__(self, **kwargs: Any) -> None:
            self.values = {"first": 1, "second": 2}

        async def get(self, key: str) -> Any:
            return self.values.get(key)

        async def set(
            self, key: str, value: Any, debug_data: dict | None = None
        ) -> None:
            self.values[key] = value

        async def has(self, key: str) -> bool:
            return key in self.values

        async def delete(self, key: str) -> None:
            del self.values[key]

        async def clear(self) -> None:
            self.values.clear()

        def child(self, name: str) -> Cache:
            return self

    cache = CustomCache()

    assert await cache.get_many(["first", "missing", "first", "second"]) == {
        "first": 1,
        "second": 2,
    }
