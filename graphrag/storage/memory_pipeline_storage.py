# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'InMemoryStorage' model."""

import asyncio
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
        results = [(key, {}) for key in self._storage["files"]]
        return iter(results)

    async def get(
        self, key: str, as_bytes: bool | None = None, encoding: str | None = None
    ) -> pd.DataFrame | Any:
        """Get the value for the given key.

        Args:
            - key - The key to get the value for.
            - as_bytes - Whether or not to return the value as bytes.

        Returns
        -------
            - output - The value for the given key.
        """
        return self._storage["files"].get(key)

    async def set(self, key: str, value: Any, encoding: str | None = None) -> None:
        """Set the value for the given key.

        Args:
            - key - The key to set the value for.
            - value - The value to set.
        """
        if "files" not in self._storage:
            self._storage["files"] = {}

        self._storage["files"][key] = value

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

    def child(self, name: str | None) -> "PipelineStorage":
        """Create a child storage instance."""
        return self

    def keys(self) -> list[str]:
        """Return the keys in the storage."""
        return list(self._storage.keys())

    async def get_creation_date(self, key: str) -> str:
        """Get the creation date for the given key."""
        return datetime.now(timezone.utc).isoformat()

    def set_sync(self, key: str, value: Any, encoding: str | None = None) -> None:
        """Set the value for the given key.

        Args:
            - key - The key to set the value for.
            - value - The value to set.
        """
        task = asyncio.create_task(self.set(key, value, encoding))
        logger.info("Setting value for key '%s' in memory storage", task.get_name())


def create_memory_storage(**kwargs: Any) -> PipelineStorage:
    """Create a memory based storage."""
    logger.info("Creating memory storage")
    memorystorage = MemoryPipelineStorage()
    for key, value in kwargs["input_files"].items():
        memorystorage.set_sync(key, value)
    return memorystorage
