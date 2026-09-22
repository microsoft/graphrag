# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""SQLite cache implementation."""

from __future__ import annotations

import asyncio
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

from graphrag_cache.cache import Cache

if TYPE_CHECKING:
    from collections.abc import Generator


class SQLiteCache(Cache):
    """A concurrency-safe, namespaced cache backed by SQLite."""

    def __init__(
        self,
        database_path: str | Path = "cache/cache.db",
        *,
        namespace: str = "",
        **_: Any,
    ) -> None:
        """Initialize the SQLite cache."""
        self._database_path = Path(database_path)
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
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
            await self.delete(key)
            return None
        return data.get("result")

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
            database_path=self._database_path,
            namespace=namespace,
        )
