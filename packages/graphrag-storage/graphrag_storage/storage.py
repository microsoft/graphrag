# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Abstract base class for storage."""

import re
from abc import ABC, abstractmethod
from collections.abc import Iterator
from datetime import datetime
from typing import Any


class Storage(ABC):
    """Provide a storage interface."""

    @abstractmethod
    def __init__(self, **kwargs: Any) -> None:
        """Create a storage instance."""

    @abstractmethod
    def find(
        self,
        file_pattern: re.Pattern[str],
    ) -> Iterator[str]:
        """Find files in the storage using a file pattern.

        Args
        ----
            - file_pattern: re.Pattern[str]
                The file pattern to use for finding files.

        Returns
        -------
            Iterator[str]:
                An iterator over the found file keys.

        """

    @abstractmethod
    async def get(
        self, key: str, as_bytes: bool | None = None, encoding: str | None = None
    ) -> Any:
        """Get the value for the given key.

        Args
        ----
            - key: str
                The key to get the value for.
            - as_bytes: bool | None, optional (default=None)
                Whether or not to return the value as bytes.
            - encoding: str | None, optional (default=None)
                The encoding to use when decoding the value.

        Returns
        -------
            Any:
                The value for the given key.
        """

    @abstractmethod
    async def set(self, key: str, value: Any, encoding: str | None = None) -> None:
        """Set the value for the given key.

        Args
        ----
            - key: str
                The key to set the value for.
            - value: Any
                The value to set.
        """

    @abstractmethod
    async def has(self, key: str) -> bool:
        """Return True if the given key exists in the storage.

        Args
        ----
            - key: str
                The key to check for.

        Returns
        -------
            bool:
                True if the key exists in the storage, False otherwise.
        """

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete the given key from the storage.

        Args
        ----
            - key: str
                The key to delete.
        """

    @abstractmethod
    async def clear(self) -> None:
        """Clear the storage."""

    @abstractmethod
    def child(self, name: str | None) -> "Storage":
        """Create a child storage instance.

        Args
        ----
            - name: str | None
                The name of the child storage.

        Returns
        -------
            Storage
                The child storage instance.

        """

    @abstractmethod
    def keys(self) -> list[str]:
        """List all keys in the storage."""

    @abstractmethod
    async def get_creation_date(self, key: str) -> str:
        """Get the creation date for the given key.

        Args
        ----
            - key: str
                The key to get the creation date for.

        Returns
        -------
            str:
                The creation date for the given key.
        """


def get_timestamp_formatted_with_local_tz(timestamp: datetime) -> str:
    """Get the formatted timestamp with the local time zone."""
    creation_time_local = timestamp.astimezone()

    return creation_time_local.strftime("%Y-%m-%d %H:%M:%S %z")
