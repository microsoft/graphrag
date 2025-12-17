# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'JsonCache' model."""

import json
from typing import Any

from graphrag_storage import Storage, StorageConfig, create_storage

from graphrag_cache.cache import Cache


class JsonCache(Cache):
    """File pipeline cache class definition."""

    _storage: Storage

    def __init__(
        self,
        storage: Storage | dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Init method definition."""
        if storage is None:
            msg = "JsonCache requires either a Storage instance to be provided or a StorageConfig to create one."
            raise ValueError(msg)
        if isinstance(storage, Storage):
            self._storage = storage
        else:
            self._storage = create_storage(StorageConfig(**storage))

    async def get(self, key: str) -> Any | None:
        """Get method definition."""
        if await self.has(key):
            try:
                data = await self._storage.get(key)
                data = json.loads(data)
            except UnicodeDecodeError:
                await self._storage.delete(key)
                return None
            except json.decoder.JSONDecodeError:
                await self._storage.delete(key)
                return None
            else:
                return data.get("result")

        return None

    async def set(self, key: str, value: Any, debug_data: dict | None = None) -> None:
        """Set method definition."""
        if value is None:
            return
        data = {"result": value, **(debug_data or {})}
        await self._storage.set(key, json.dumps(data, ensure_ascii=False))

    async def has(self, key: str) -> bool:
        """Has method definition."""
        return await self._storage.has(key)

    async def delete(self, key: str) -> None:
        """Delete method definition."""
        if await self.has(key):
            await self._storage.delete(key)

    async def clear(self) -> None:
        """Clear method definition."""
        await self._storage.clear()

    def child(self, name: str) -> "Cache":
        """Child method definition."""
        return JsonCache(storage=self._storage.child(name))
