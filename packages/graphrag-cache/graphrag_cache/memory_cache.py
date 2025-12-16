# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""MemoryCache implementation."""

from typing import Any

from graphrag_cache.cache import Cache


class MemoryCache(Cache):
    """In memory cache class definition."""

    _cache: dict[str, Any]
    _name: str

    def __init__(self, **kwargs: Any) -> None:
        """Init method definition."""
        self._cache = {}

    async def get(self, key: str) -> Any:
        """Get the value for the given key.

        Args:
            - key - The key to get the value for.
            - as_bytes - Whether or not to return the value as bytes.

        Returns
        -------
            - output - The value for the given key.
        """
        return self._cache.get(key)

    async def set(self, key: str, value: Any, debug_data: dict | None = None) -> None:
        """Set the value for the given key.

        Args:
            - key - The key to set the value for.
            - value - The value to set.
        """
        self._cache[key] = value

    async def has(self, key: str) -> bool:
        """Return True if the given key exists in the storage.

        Args:
            - key - The key to check for.

        Returns
        -------
            - output - True if the key exists in the storage, False otherwise.
        """
        return key in self._cache

    async def delete(self, key: str) -> None:
        """Delete the given key from the storage.

        Args:
            - key - The key to delete.
        """
        del self._cache[key]

    async def clear(self) -> None:
        """Clear the storage."""
        self._cache.clear()

    def child(self, name: str) -> "Cache":
        """Create a sub cache with the given name."""
        return MemoryCache()
