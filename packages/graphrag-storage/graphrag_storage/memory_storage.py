# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""In-memory storage implementation."""

import re
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from graphrag_storage.file_storage import FileStorage

if TYPE_CHECKING:
    from graphrag_storage.storage import Storage


class MemoryStorage(FileStorage):
    """In memory storage class definition."""

    _storage: dict[str, Any]

    def __init__(self, **kwargs: Any) -> None:
        """Init method definition."""
        kwargs = {
            "base_dir": "",
            **kwargs,
        }
        kwargs.pop("type", None)
        super().__init__(**kwargs)
        self._storage = {}

    async def get(
        self, key: str, as_bytes: bool | None = None, encoding: str | None = None
    ) -> Any:
        """Get the value for the given key.

        Args:
            - key - The key to get the value for.
            - as_bytes - Whether or not to return the value as bytes.

        Returns
        -------
            - output - The value for the given key.
        """
        return self._storage.get(key)

    async def set(self, key: str, value: Any, encoding: str | None = None) -> None:
        """Set the value for the given key.

        Args:
            - key - The key to set the value for.
            - value - The value to set.
        """
        self._storage[key] = value

    async def has(self, key: str) -> bool:
        """Return True if the given key exists in the storage.

        Args:
            - key - The key to check for.

        Returns
        -------
            - output - True if the key exists in the storage, False otherwise.
        """
        return key in self._storage

    async def delete(self, key: str) -> None:
        """Delete the given key from the storage.

        Args:
            - key - The key to delete.
        """
        del self._storage[key]

    async def clear(self) -> None:
        """Clear the storage."""
        self._storage.clear()

    def child(self, name: str | None) -> "Storage":
        """Create a child storage instance."""
        return MemoryStorage()

    def keys(self) -> list[str]:
        """Return the keys in the storage."""
        return list(self._storage.keys())

    def find(self, file_pattern: re.Pattern[str]) -> Iterator[str]:
        """Find keys in memory storage matching the given pattern.

        Args
        ----
            file_pattern: re.Pattern[str]
                Regular expression pattern to match against keys.

        Yields
        ------
            str:
                Keys that match the pattern.
        """
        for key in self._storage:
            if file_pattern.search(key):
                yield key
