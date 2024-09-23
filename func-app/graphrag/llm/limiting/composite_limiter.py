# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing Composite Limiter class definition."""

from .llm_limiter import LLMLimiter


class CompositeLLMLimiter(LLMLimiter):
    """Composite Limiter class definition."""

    _limiters: list[LLMLimiter]

    def __init__(self, limiters: list[LLMLimiter]):
        """Init method definition."""
        self._limiters = limiters

    @property
    def needs_token_count(self) -> bool:
        """Whether this limiter needs the token count to be passed in."""
        return any(limiter.needs_token_count for limiter in self._limiters)

    async def acquire(self, num_tokens: int = 1) -> None:
        """Call method definition."""
        for limiter in self._limiters:
            await limiter.acquire(num_tokens)
