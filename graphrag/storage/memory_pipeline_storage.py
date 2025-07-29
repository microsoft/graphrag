# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'InMemoryStorage' model."""

import logging
import re
from collections.abc import Iterator
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from graphrag.storage.file_pipeline_storage import PipelineStorage

logger = logging.getLogger(__name__)


class MemoryPipelineStorage(PipelineStorage):
    """In memory storage class definition."""

    _storage: dict[str, Any]
    files_key: str = "files"

    def __init__(self):
        """Init method definition."""
        self._storage = {}

    def find(
        self,
        file_pattern: re.Pattern[str],
        base_dir: str | None = None,
        file_filter: dict[str, Any] | None = None,
        max_count=-1,
    ) -> Iterator[tuple[str, dict[str, Any]]]:
        """Find files in the storage using a file pattern, as well as a custom filter function."""
        # In-memory storage does not support file finding
        results: list[tuple[str, dict[str, Any]]] = []
        if self._storage.get(self.files_key) is not None:
            results = [(key, {}) for key in self._storage[self.files_key]]
        return iter(results)

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
        if self.files_key not in self._storage:
            return None
        val = self._storage[self.files_key].get(key)
        if as_bytes and val is not None and not isinstance(val, bytes):
            if isinstance(val, str):
                val = val.encode(encoding or "utf-8")
            elif isinstance(val, pd.DataFrame):
                val = val.to_csv(index=False).encode(encoding or "utf-8")
            else:
                val = bytes(val)

        return val

    async def set(self, key: str, value: Any, encoding: str | None = None) -> None:
        """Set the value for the given key.

        Args:
            - key - The key to set the value for.
            - value - The value to set.
        """
        if self.files_key not in self._storage:
            self._storage[self.files_key] = {}

        self._storage[self.files_key][key] = value

    async def has(self, key: str) -> bool:
        """Return True if the given key exists in the storage.

        Args:
            - key - The key to check for.

        Returns
        -------
            - output - True if the key exists in the storage, False otherwise.
        """
        return (
            key in self._storage[self.files_key]
            if self.files_key in self._storage
            else False
        )

    async def delete(self, key: str) -> None:
        """Delete the given key from the storage.

        Args:
            - key - The key to delete.
        """
        del self._storage[self.files_key][key]

    async def clear(self) -> None:
        """Clear the storage."""
        self._storage.clear()

    def child(self, name: str | None) -> "PipelineStorage":
        """Create a child storage instance."""
        return self

    def keys(self) -> list[str]:
        """Return the keys in the storage."""
        if self.files_key not in self._storage:
            return []
        # Return the keys of the 'files' dictionary
        return list(self._storage[self.files_key].keys())

    async def get_creation_date(self, key: str) -> str:
        """Get the creation date for the given key."""
        return datetime.now(timezone.utc).isoformat()

    def set_sync(self, key: str, value: Any, encoding: str | None = None) -> None:
        """Set the value for the given key.

        Args:
            - key - The key to set the value for.
            - value - The value to set.
        """
        logger.info("Setting value for key '%s' in memory storage", key)
        if self.files_key not in self._storage:
            self._storage[self.files_key] = {}
        self._storage[self.files_key][key] = value


def create_memory_storage(**kwargs: Any) -> PipelineStorage:
    """Create a memory based storage."""
    logger.info("Creating memory storage")
    memorystorage = MemoryPipelineStorage()
    if kwargs.get("input_files") is None:
        return memorystorage

    for key, value in kwargs["input_files"].items():
        memorystorage.set_sync(key, value)
    return memorystorage
