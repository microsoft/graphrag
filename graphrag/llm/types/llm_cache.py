# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Typing definitions for the OpenAI DataShaper package."""

from typing import Any, Protocol


class LLMCache(Protocol):
    """LLM Cache interface."""

    async def has(self, key: str) -> bool:
        """Check if the cache has a value."""
        ...

    async def get(self, key: str) -> Any | None:
        """Retrieve a value from the cache."""
        ...

    async def set(self, key: str, value: Any, debug_data: dict | None = None) -> None:
        """Write a value into the cache."""
        ...
