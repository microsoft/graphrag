# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""LiteLLM Static Rate Limiter."""

import threading
import time
from collections import deque
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from graphrag.language_model.providers.litellm.services.rate_limiter.rate_limiter import (
    RateLimiter,
)


class StaticRateLimiter(RateLimiter):
    """Static Rate Limiter implementation."""

    def __init__(
        self,
        *,
        rpm: int | None = None,
        tpm: int | None = None,
        default_stagger: float = 0.0,
        period_in_seconds: int = 60,
        **kwargs: Any,
    ):
        if rpm is None and tpm is None:
            msg = "Both TPM and RPM cannot be None (disabled), one or both must be set to a positive integer."
            raise ValueError(msg)
        if (rpm is not None and rpm <= 0) or (tpm is not None and tpm <= 0):
            msg = "RPM and TPM must be either None (disabled) or positive integers."
            raise ValueError(msg)
        if default_stagger < 0:
            msg = "Default stagger must be a >= 0."
            raise ValueError(msg)
        if period_in_seconds <= 0:
            msg = "Period in seconds must be a positive integer."
            raise ValueError(msg)
        self.rpm = rpm
        self.tpm = tpm
        self._lock = threading.Lock()
        self.rate_queue: deque[float] = deque()
        self.token_queue: deque[int] = deque()
        self.period_in_seconds = period_in_seconds
        self._last_time: float | None = None

        self.stagger = default_stagger
        if self.rpm is not None and self.rpm > 0:
            self.stagger = self.period_in_seconds / self.rpm

    @contextmanager
    def acquire(self, *, token_count: int) -> Iterator[None]:
        """
        Acquire Rate Limiter.

        Args
        ----
            token_count: The estimated number of tokens for the current request.

        Yields
        ------
            None: This context manager does not return any value.
        """
        while True:
            with self._lock:
                current_time = time.time()

                # Use two sliding windows to keep track of #requests and tokens per period
                # Drop old requests and tokens out of the sliding windows
                while (
                    len(self.rate_queue) > 0
                    and self.rate_queue[0] < current_time - self.period_in_seconds
                ):
                    self.rate_queue.popleft()
                    self.token_queue.popleft()

                # If sliding window still exceed request limit, wait again
                # Waiting requires reacquiring the lock, allowing other threads
                # to see if their request fits within the rate limiting windows
                # Makes more sense for token limit than request limit
                if (
                    self.rpm is not None
                    and self.rpm > 0
                    and len(self.rate_queue) >= self.rpm
                ):
                    continue

                # Check if current token window exceeds token limit
                # If it does, wait again
                # This does not account for the tokens from the current request
                # This is intentional, as we want to allow the current request
                # to be processed if it is larger than the tpm but smaller than context window.
                # tpm is a rate/soft limit and not the hard limit of context window limits.
                if (
                    self.tpm is not None
                    and self.tpm > 0
                    and sum(self.token_queue) >= self.tpm
                ):
                    continue

                # This check accounts for the current request token usage
                # is within the token limits bound.
                # If the current requests token limit exceeds the token limit,
                # Then let it be processed.
                if (
                    self.tpm is not None
                    and self.tpm > 0
                    and token_count <= self.tpm
                    and sum(self.token_queue) + token_count > self.tpm
                ):
                    continue

                # If there was a previous call, check if we need to stagger
                if (
                    self.stagger > 0
                    and (
                        self._last_time  # is None if this is the first hit to the rate limiter
                        and current_time - self._last_time
                        < self.stagger  # If more time has passed than the stagger time, we can proceed
                    )
                ):
                    time.sleep(self.stagger - (current_time - self._last_time))
                    current_time = time.time()

                # Add the current request to the sliding window
                self.rate_queue.append(current_time)
                self.token_queue.append(token_count)
                self._last_time = current_time
                break
        yield
