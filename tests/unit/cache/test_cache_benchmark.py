# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Opt-in benchmarks for cache bulk reads."""

import gc
from dataclasses import dataclass
from statistics import median
from time import perf_counter

import pytest
from graphrag_cache.cache import Cache
from graphrag_cache.json_cache import JsonCache
from graphrag_cache.memory_cache import MemoryCache
from graphrag_cache.sqlite_cache import SQLiteCache
from graphrag_storage.file_storage import FileStorage

ENTRY_COUNT = 1_000
MEASUREMENT_ROUNDS = 7


@dataclass(frozen=True)
class BenchmarkResult:
    """Summarize one cache backend measurement."""

    name: str
    median_seconds: float

    @property
    def entries_per_second(self) -> float:
        """Return median bulk-read throughput."""
        return ENTRY_COUNT / self.median_seconds


async def _populate(cache: Cache, keys: list[str]) -> None:
    value = {
        "text": "Representative cached response",
        "items": list(range(10)),
        "metadata": {"cached": True},
    }
    for index, key in enumerate(keys):
        await cache.set(key, {**value, "index": index})


async def _measure(cache: Cache, keys: list[str], name: str) -> BenchmarkResult:
    expected_keys = set(keys)
    assert set(await cache.get_many(keys)) == expected_keys

    durations = []
    for _ in range(MEASUREMENT_ROUNDS):
        gc.collect()
        start = perf_counter()
        result = await cache.get_many(keys)
        durations.append(perf_counter() - start)
        assert set(result) == expected_keys

    return BenchmarkResult(name=name, median_seconds=median(durations))


@pytest.mark.asyncio
async def test_bulk_read_cache_benchmark(tmp_path, pytestconfig):
    """Report warm bulk-read throughput without a machine-dependent threshold."""
    if not pytestconfig.getoption("run_cache_benchmark"):
        pytest.skip("use --run-cache-benchmark to run performance measurements")

    keys = [f"key-{index}" for index in range(ENTRY_COUNT)]
    caches: list[tuple[str, Cache]] = [
        ("Memory", MemoryCache()),
        (
            "JSON",
            JsonCache(storage=FileStorage(base_dir=str(tmp_path / "json-cache"))),
        ),
        (
            "SQLite",
            SQLiteCache(FileStorage(base_dir=str(tmp_path / "sqlite-cache"))),
        ),
    ]

    results = []
    for name, cache in caches:
        await _populate(cache, keys)
        results.append(await _measure(cache, keys, name))

    sqlite_seconds = next(
        result.median_seconds for result in results if result.name == "SQLite"
    )
    print(
        f"\nWarm get_many benchmark: {ENTRY_COUNT:,} entries, "
        f"median of {MEASUREMENT_ROUNDS} rounds"
    )
    print("Backend       Median (ms)    Entries/sec    Time vs SQLite")
    for result in results:
        print(
            f"{result.name:<13}"
            f"{result.median_seconds * 1_000:>11.2f}"
            f"{result.entries_per_second:>15,.0f}"
            f"{result.median_seconds / sqlite_seconds:>16.2f}x"
        )
