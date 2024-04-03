# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Limiting types."""

from abc import ABC, abstractmethod


class LLMLimiter(ABC):
    """LLM Limiter Interface."""

    @property
    @abstractmethod
    def needs_token_count(self) -> bool:
        """Whether this limiter needs the token count to be passed in."""

    @abstractmethod
    async def acquire(self, num_tokens: int = 1) -> None:
        """Acquire a pass through the limiter."""
