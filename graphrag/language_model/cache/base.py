# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""Base cache protocol definition."""

from typing import Any, Protocol


class ModelCache(Protocol):
    """Base cache protocol."""

    async def has(self, key: str) -> bool:
        """Check if the cache has a value."""
        ...

    async def get(self, key: str) -> Any | None:
        """Retrieve a value from the cache."""
        ...

    async def set(
        self, key: str, value: Any, metadata: dict[str, Any] | None = None
    ) -> None:
        """Write a value into the cache."""
        ...

    async def remove(self, key: str) -> None:
        """Remove a value from the cache."""
        ...

    async def clear(self) -> None:
        """Clear the cache."""
        ...

    def child(self, key: str) -> Any:
        """Create a child cache."""
        ...
