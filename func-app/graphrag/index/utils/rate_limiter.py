# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Rate limiter utility."""

import asyncio
import time


class RateLimiter:
    """
    The original TpmRpmLLMLimiter strategy did not account for minute-based rate limiting when scheduled.

    The RateLimiter was introduced to ensure that the CommunityReportsExtractor could be scheduled to adhere to rate configurations on a per-minute basis.
    """

    # TODO: RateLimiter scheduled: using asyncio for async_mode

    def __init__(self, rate: int, per: int):
        self.rate = rate
        self.per = per
        self.allowance = rate
        self.last_check = time.monotonic()

    async def acquire(self):
        """Acquire a token from the rate limiter."""
        current = time.monotonic()
        elapsed = current - self.last_check
        self.last_check = current
        self.allowance += elapsed * (self.rate / self.per)

        if self.allowance > self.rate:
            self.allowance = self.rate

        if self.allowance < 1.0:
            sleep_time = (1.0 - self.allowance) * (self.per / self.rate)
            await asyncio.sleep(sleep_time)
            self.allowance = 0.0
        else:
            self.allowance -= 1.0
