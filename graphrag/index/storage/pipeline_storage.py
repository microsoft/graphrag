# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'PipelineStorage' model."""

import re
from abc import ABCMeta, abstractmethod
from collections.abc import Iterator
from typing import Any

from graphrag.logging.base import ProgressReporter


class PipelineStorage(metaclass=ABCMeta):
    """Provide a storage interface for the pipeline. This is where the pipeline will store its output data."""

    @abstractmethod
    def find(
        self,
        file_pattern: re.Pattern[str],
        base_dir: str | None = None,
        progress: ProgressReporter | None = None,
        file_filter: dict[str, Any] | None = None,
        max_count=-1,
    ) -> Iterator[tuple[str, dict[str, Any]]]:
        """Find files in the storage using a file pattern, as well as a custom filter function."""

    @abstractmethod
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

    @abstractmethod
    async def set(self, key: str, value: Any, encoding: str | None = None) -> None:
        """Set the value for the given key.

        Args:
            - key - The key to set the value for.
            - value - The value to set.
        """

    @abstractmethod
    async def has(self, key: str) -> bool:
        """Return True if the given key exists in the storage.

        Args:
            - key - The key to check for.

        Returns
        -------
            - output - True if the key exists in the storage, False otherwise.
        """

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete the given key from the storage.

        Args:
            - key - The key to delete.
        """

    @abstractmethod
    async def clear(self) -> None:
        """Clear the storage."""

    @abstractmethod
    def child(self, name: str | None) -> "PipelineStorage":
        """Create a child storage instance."""

    @abstractmethod
    def keys(self) -> list[str]:
        """List all keys in the storage."""
