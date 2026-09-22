# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Tests for the SQLite cache."""

import asyncio
import json
import sqlite3

import pytest
from graphrag_cache import CacheConfig, CacheType
from graphrag_cache.sqlite_cache import SQLiteCache
from graphrag_storage import StorageConfig, StorageType
from graphrag_storage.file_storage import FileStorage
from graphrag_storage.memory_storage import MemoryStorage
from pydantic import ValidationError


@pytest.mark.asyncio
async def test_sqlite_cache_round_trip_and_persistence(tmp_path):
    storage = FileStorage(base_dir=str(tmp_path))
    cache = SQLiteCache(storage)

    await cache.set("key", {"text": "héllo", "items": [1, 2, 3]})

    assert await cache.has("key")
    assert await cache.get("key") == {"text": "héllo", "items": [1, 2, 3]}
    assert await SQLiteCache(storage).get("key") == {
        "text": "héllo",
        "items": [1, 2, 3],
    }


@pytest.mark.asyncio
async def test_sqlite_cache_overwrites_and_deletes_values(tmp_path):
    cache = SQLiteCache(FileStorage(base_dir=str(tmp_path)))

    await cache.set("key", "first")
    await cache.set("key", "second")
    await cache.set("ignored", None)

    assert await cache.get("key") == "second"
    assert not await cache.has("ignored")

    await cache.delete("key")

    assert not await cache.has("key")
    assert await cache.get("key") is None


@pytest.mark.asyncio
async def test_sqlite_cache_child_namespaces_are_isolated(tmp_path):
    cache = SQLiteCache(FileStorage(base_dir=str(tmp_path)))
    first_child = cache.child("first")
    second_child = cache.child("second")

    await cache.set("key", "root")
    await first_child.set("key", "first")
    await second_child.set("key", "second")
    await first_child.clear()

    assert await cache.get("key") == "root"
    assert await first_child.get("key") is None
    assert await second_child.get("key") == "second"


@pytest.mark.asyncio
async def test_sqlite_cache_supports_concurrent_writes(tmp_path):
    cache = SQLiteCache(FileStorage(base_dir=str(tmp_path)))

    await asyncio.gather(*(cache.set(f"key-{index}", index) for index in range(20)))

    assert await asyncio.gather(
        *(cache.get(f"key-{index}") for index in range(20))
    ) == list(range(20))


@pytest.mark.parametrize(
    "payload",
    [
        "not json",
        "[]",
        '"value"',
        "null",
        '{"debug": "missing result"}',
    ],
)
@pytest.mark.asyncio
async def test_sqlite_cache_removes_invalid_payload(tmp_path, payload):
    database_path = tmp_path / "cache.db"
    cache = SQLiteCache(FileStorage(base_dir=str(tmp_path)))
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO cache_entries(namespace, key, value_json)
            VALUES (?, ?, ?)
            """,
            ("", "invalid", payload),
        )

    assert await cache.get("invalid") is None
    assert not await cache.has("invalid")


@pytest.mark.asyncio
async def test_corruption_cleanup_preserves_newer_value(tmp_path):
    class ReplacingSQLiteCache(SQLiteCache):
        def _delete_if_unchanged(self, key: str, payload: str) -> None:
            self._set(key, json.dumps({"result": "replacement"}))
            super()._delete_if_unchanged(key, payload)

    database_path = tmp_path / "cache.db"
    cache = ReplacingSQLiteCache(FileStorage(base_dir=str(tmp_path)))
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO cache_entries(namespace, key, value_json)
            VALUES (?, ?, ?)
            """,
            ("", "invalid", "not json"),
        )

    assert await cache.get("invalid") is None
    assert await cache.get("invalid") == "replacement"


def test_sqlite_cache_uses_database_name_within_storage(tmp_path):
    cache = SQLiteCache(
        FileStorage(base_dir=str(tmp_path)),
        database_name="custom.db",
    )

    assert (tmp_path / "custom.db").exists()
    assert isinstance(cache, SQLiteCache)


@pytest.mark.parametrize(
    "database_name",
    [
        "/tmp/cache.db",
        "../cache.db",
        "nested/cache.db",
        r"C:\temp\cache.db",
        r"..\cache.db",
        ".",
        "..",
    ],
)
def test_sqlite_cache_rejects_database_path(tmp_path, database_name):
    with pytest.raises(
        ValueError,
        match="database_name must be a file name without a directory",
    ):
        SQLiteCache(
            FileStorage(base_dir=str(tmp_path)),
            database_name=database_name,
        )


def test_sqlite_cache_rejects_non_file_storage():
    with pytest.raises(TypeError, match="only supports FileStorage"):
        SQLiteCache(MemoryStorage())


@pytest.mark.parametrize(
    "storage_type",
    [
        StorageType.Memory,
        StorageType.AzureBlob,
        StorageType.AzureCosmos,
    ],
)
def test_sqlite_cache_config_rejects_non_file_storage(storage_type):
    with pytest.raises(
        ValidationError,
        match="Cache type 'sqlite' requires storage type 'file'",
    ):
        CacheConfig(
            type=CacheType.Sqlite,
            storage=StorageConfig(type=storage_type),
        )


def test_sqlite_cache_config_requires_storage():
    with pytest.raises(
        ValidationError,
        match="Cache type 'sqlite' requires storage type 'file'",
    ):
        CacheConfig(type=CacheType.Sqlite, storage=None)
