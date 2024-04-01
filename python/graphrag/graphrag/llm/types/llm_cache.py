#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

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
