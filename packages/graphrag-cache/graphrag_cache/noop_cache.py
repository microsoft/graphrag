# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""NoopCache implementation."""

from typing import Any

from graphrag_cache.cache import Cache


class NoopCache(Cache):
    """A no-op implementation of Cache, usually useful for testing."""

    def __init__(self, **kwargs: Any) -> None:
        """Init method definition."""

    async def get(self, key: str) -> Any:
        """Get the value for the given key.

        Args:
            - key - The key to get the value for.
            - as_bytes - Whether or not to return the value as bytes.

        Returns
        -------
            - output - The value for the given key.
        """
        return None

    async def set(
        self, key: str, value: str | bytes | None, debug_data: dict | None = None
    ) -> None:
        """Set the value for the given key.

        Args:
            - key - The key to set the value for.
            - value - The value to set.
        """

    async def has(self, key: str) -> bool:
        """Return True if the given key exists in the cache.

        Args:
            - key - The key to check for.

        Returns
        -------
            - output - True if the key exists in the cache, False otherwise.
        """
        return False

    async def delete(self, key: str) -> None:
        """Delete the given key from the cache.

        Args:
            - key - The key to delete.
        """

    async def clear(self) -> None:
        """Clear the cache."""

    def child(self, name: str) -> "Cache":
        """Create a child cache with the given name.

        Args:
            - name - The name to create the sub cache with.
        """
        return self
