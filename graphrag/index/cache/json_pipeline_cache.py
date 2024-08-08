# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'FilePipelineCache' model."""

import json
from typing import Any

from graphrag.index.storage import PipelineStorage

from .pipeline_cache import PipelineCache


class JsonPipelineCache(PipelineCache):
    """File pipeline cache class definition."""

    _storage: PipelineStorage
    _encoding: str

    def __init__(self, storage: PipelineStorage, encoding="utf-8"):
        """Init method definition."""
        self._storage = storage
        self._encoding = encoding

    async def get(self, key: str) -> str | None:
        """Get method definition."""
        if await self.has(key):
            try:
                data = await self._storage.get(key, encoding=self._encoding)
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
        await self._storage.set(
            key, json.dumps(data, ensure_ascii=False), encoding=self._encoding
        )

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

    def child(self, name: str) -> "JsonPipelineCache":
        """Child method definition."""
        return JsonPipelineCache(self._storage.child(name), encoding=self._encoding)
