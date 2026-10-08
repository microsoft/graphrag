# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Tests for the SQLite cache."""

import asyncio
import json
import sqlite3
from contextlib import contextmanager
from math import ceil

import pytest
from graphrag_cache import CacheConfig, CacheType
from graphrag_cache.sqlite_cache import SQLITE_BATCH_SIZE, SQLiteCache
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


@pytest.mark.asyncio
async def test_sqlite_cache_get_many_batches_with_one_thread_and_connection(
    tmp_path, monkeypatch
):
    cache = SQLiteCache(FileStorage(base_dir=str(tmp_path)))
    key_count = SQLITE_BATCH_SIZE * 2 + 37
    with sqlite3.connect(tmp_path / "cache.db") as connection:
        connection.executemany(
            """
            INSERT INTO cache_entries(namespace, key, value_json)
            VALUES (?, ?, ?)
            """,
            (
                ("", f"key-{index}", json.dumps({"result": index}))
                for index in range(key_count)
            ),
        )

    thread_dispatches = 0
    connection_count = 0
    select_count = 0
    original_to_thread = asyncio.to_thread
    original_connect = cache._connect  # noqa: SLF001

    async def counting_to_thread(func, /, *args, **kwargs):
        nonlocal thread_dispatches
        thread_dispatches += 1
        return await original_to_thread(func, *args, **kwargs)

    @contextmanager
    def counting_connect():
        nonlocal connection_count
        connection_count += 1
        with original_connect() as connection:

            def count_select(statement):
                nonlocal select_count
                if "SELECT key, value_json" in statement:
                    select_count += 1

            connection.set_trace_callback(count_select)
            yield connection

    monkeypatch.setattr(
        "graphrag_cache.sqlite_cache.asyncio.to_thread", counting_to_thread
    )
    monkeypatch.setattr(cache, "_connect", counting_connect)

    keys = [f"key-{index}" for index in range(key_count)]
    result = await cache.get_many([*keys, "missing", keys[0]])

    assert result == {f"key-{index}": index for index in range(key_count)}
    assert thread_dispatches == 1
    assert connection_count == 1
    assert select_count == ceil((key_count + 1) / SQLITE_BATCH_SIZE)


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


@pytest.mark.asyncio
async def test_get_many_removes_invalid_payloads(tmp_path):
    cache = SQLiteCache(FileStorage(base_dir=str(tmp_path)))
    with sqlite3.connect(tmp_path / "cache.db") as connection:
        connection.executemany(
            """
            INSERT INTO cache_entries(namespace, key, value_json)
            VALUES (?, ?, ?)
            """,
            [
                ("", "valid", '{"result": {"value": 1}}'),
                ("", "invalid-json", "not json"),
                ("", "invalid-envelope", '{"debug": true}'),
            ],
        )

    assert await cache.get_many(["valid", "invalid-json", "invalid-envelope"]) == {
        "valid": {"value": 1}
    }
    assert not await cache.has("invalid-json")
    assert not await cache.has("invalid-envelope")


@pytest.mark.asyncio
async def test_get_many_corruption_cleanup_preserves_newer_value(tmp_path):
    class ReplacingSQLiteCache(SQLiteCache):
        def _delete_many_if_unchanged(self, connection, entries):
            self._set("invalid", json.dumps({"result": "replacement"}))
            super()._delete_many_if_unchanged(connection, entries)

    cache = ReplacingSQLiteCache(FileStorage(base_dir=str(tmp_path)))
    with sqlite3.connect(tmp_path / "cache.db") as connection:
        connection.execute(
            """
            INSERT INTO cache_entries(namespace, key, value_json)
            VALUES (?, ?, ?)
            """,
            ("", "invalid", "not json"),
        )

    assert await cache.get_many(["invalid"]) == {}
    assert await cache.get("invalid") == "replacement"


@pytest.mark.asyncio
async def test_get_many_supports_concurrent_reader_and_writer(tmp_path):
    cache = SQLiteCache(FileStorage(base_dir=str(tmp_path)))
    await asyncio.gather(
        *(cache.set(f"key-{index}", index) for index in range(20)),
        cache.get_many([f"key-{index}" for index in range(20)]),
    )

    assert await cache.get_many([f"key-{index}" for index in range(20)]) == {
        f"key-{index}": index for index in range(20)
    }


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
