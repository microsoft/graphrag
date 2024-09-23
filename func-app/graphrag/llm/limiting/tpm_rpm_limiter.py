# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""TPM RPM Limiter module."""

from aiolimiter import AsyncLimiter

from .llm_limiter import LLMLimiter


class TpmRpmLLMLimiter(LLMLimiter):
    """TPM RPM Limiter class definition."""

    _tpm_limiter: AsyncLimiter | None
    _rpm_limiter: AsyncLimiter | None

    def __init__(
        self, tpm_limiter: AsyncLimiter | None, rpm_limiter: AsyncLimiter | None
    ):
        """Init method definition."""
        self._tpm_limiter = tpm_limiter
        self._rpm_limiter = rpm_limiter

    @property
    def needs_token_count(self) -> bool:
        """Whether this limiter needs the token count to be passed in."""
        return self._tpm_limiter is not None

    async def acquire(self, num_tokens: int = 1) -> None:
        """Call method definition."""
        if self._tpm_limiter is not None:
            await self._tpm_limiter.acquire(num_tokens)
        if self._rpm_limiter is not None:
            await self._rpm_limiter.acquire()
