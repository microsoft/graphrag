# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""TPM RPM Limiter module."""

from .llm_limiter import LLMLimiter


class NoopLLMLimiter(LLMLimiter):
    """TPM RPM Limiter class definition."""

    @property
    def needs_token_count(self) -> bool:
        """Whether this limiter needs the token count to be passed in."""
        return False

    async def acquire(self, num_tokens: int = 1) -> None:
        """Call method definition."""
        # do nothing
