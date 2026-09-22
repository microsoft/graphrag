# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""SQLite cache implementation."""

from __future__ import annotations

import asyncio
import json
import sqlite3
from contextlib import contextmanager
from pathlib import PurePosixPath, PureWindowsPath
from typing import TYPE_CHECKING, Any

from graphrag_storage import Storage, StorageConfig, create_storage
from graphrag_storage.file_storage import FileStorage
from graphrag_storage.memory_storage import MemoryStorage

from graphrag_cache.cache import Cache

if TYPE_CHECKING:
    from collections.abc import Generator


class SQLiteCache(Cache):
    """A concurrency-safe, namespaced cache backed by SQLite."""

    def __init__(
        self,
        storage: Storage | dict[str, Any] | None = None,
        database_name: str = "cache.db",
        *,
        namespace: str = "",
        **_: Any,
    ) -> None:
        """Initialize the SQLite cache."""
        if storage is None:
            msg = "SQLiteCache requires either a Storage instance to be provided or a StorageConfig to create one."
            raise ValueError(msg)
        if not isinstance(storage, Storage):
            storage = create_storage(StorageConfig(**storage))
        if not isinstance(storage, FileStorage) or isinstance(storage, MemoryStorage):
            msg = "SQLiteCache only supports FileStorage."
            raise TypeError(msg)
        database_paths = (
            PurePosixPath(database_name),
            PureWindowsPath(database_name),
        )
        if (
            not database_name
            or database_name == ".."
            or any(
                path.is_absolute() or len(path.parts) != 1 or path.name != database_name
                for path in database_paths
            )
        ):
            msg = "SQLiteCache database_name must be a file name without a directory."
            raise ValueError(msg)
        self._storage = storage
        self._database_name = database_name
        self._database_path = storage.get_path(database_name)
        self._namespace = namespace
        self._initialize()

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection]:
        connection = sqlite3.connect(self._database_path, timeout=30)
        connection.execute("PRAGMA busy_timeout = 30000")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA synchronous = NORMAL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS cache_entries (
                    namespace TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value_json TEXT NOT NULL,
                    PRIMARY KEY (namespace, key)
                )
                """
            )

    async def get(self, key: str) -> Any | None:
        """Get the value for the given key."""
        payload = await asyncio.to_thread(self._get, key)
        if payload is None:
            return None
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            await asyncio.to_thread(self._delete_if_unchanged, key, payload)
            return None
        if not isinstance(data, dict) or "result" not in data:
            await asyncio.to_thread(self._delete_if_unchanged, key, payload)
            return None
        return data["result"]

    def _get(self, key: str) -> str | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT value_json
                FROM cache_entries
                WHERE namespace = ? AND key = ?
                """,
                (self._namespace, key),
            ).fetchone()
        return str(row[0]) if row is not None else None

    async def set(self, key: str, value: Any, debug_data: dict | None = None) -> None:
        """Set the value for the given key."""
        if value is None:
            return
        data = {"result": value, **(debug_data or {})}
        payload = json.dumps(data, ensure_ascii=False)
        await asyncio.to_thread(self._set, key, payload)

    def _set(self, key: str, payload: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO cache_entries(namespace, key, value_json)
                VALUES (?, ?, ?)
                ON CONFLICT(namespace, key)
                DO UPDATE SET value_json = excluded.value_json
                """,
                (self._namespace, key, payload),
            )

    async def has(self, key: str) -> bool:
        """Return whether the given key exists in the cache."""
        return await asyncio.to_thread(self._has, key)

    def _has(self, key: str) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT 1
                FROM cache_entries
                WHERE namespace = ? AND key = ?
                """,
                (self._namespace, key),
            ).fetchone()
        return row is not None

    async def delete(self, key: str) -> None:
        """Delete the given key from the cache."""
        await asyncio.to_thread(self._delete, key)

    def _delete(self, key: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM cache_entries WHERE namespace = ? AND key = ?",
                (self._namespace, key),
            )

    def _delete_if_unchanged(self, key: str, payload: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                DELETE FROM cache_entries
                WHERE namespace = ? AND key = ? AND value_json = ?
                """,
                (self._namespace, key, payload),
            )

    async def clear(self) -> None:
        """Clear this cache namespace."""
        await asyncio.to_thread(self._clear)

    def _clear(self) -> None:
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM cache_entries WHERE namespace = ?",
                (self._namespace,),
            )

    def child(self, name: str) -> Cache:
        """Create a child cache with the given name."""
        namespace = f"{self._namespace}/{name}" if self._namespace else name
        return SQLiteCache(
            storage=self._storage,
            database_name=self._database_name,
            namespace=namespace,
        )
