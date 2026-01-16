# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""LiteLLM Static Rate Limiter."""

import threading
import time
from collections import deque
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from graphrag_llm.rate_limit.rate_limiter import RateLimiter


class SlidingWindowRateLimiter(RateLimiter):
    """Sliding Window Rate Limiter implementation."""

    _rpp: int | None = None
    _tpp: int | None = None
    _lock: threading.Lock
    _rate_queue: deque[float]
    _token_queue: deque[int]
    _period_in_seconds: int
    _last_time: float | None = None
    _stagger: float = 0.0

    def __init__(
        self,
        *,
        period_in_seconds: int = 60,
        requests_per_period: int | None = None,
        tokens_per_period: int | None = None,
        **kwargs: Any,
    ):
        """Initialize the Sliding Window Rate Limiter.

        Args
        ----
            period_in_seconds: int
                The time period in seconds for rate limiting.
            requests_per_period: int | None
                The maximum number of requests allowed per time period. If None, request limiting is disabled.
            tokens_per_period: int | None
                The maximum number of tokens allowed per time period. If None, token limiting is disabled.

        Raises
        ------
            ValueError
                If period_in_seconds is not a positive integer.
                If requests_per_period or tokens_per_period are not positive integers.
        """
        self._rpp = requests_per_period
        self._tpp = tokens_per_period
        self._lock = threading.Lock()
        self._rate_queue: deque[float] = deque()
        self._token_queue: deque[int] = deque()
        self._period_in_seconds = period_in_seconds
        self._last_time: float | None = None

        if self._rpp is not None and self._rpp > 0:
            self._stagger = self._period_in_seconds / self._rpp

    @contextmanager
    def acquire(self, token_count: int) -> Iterator[None]:
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

                # Use two sliding windows to keep track of requests and tokens per period
                # Drop old requests and tokens out of the sliding windows
                while (
                    len(self._rate_queue) > 0
                    and self._rate_queue[0] < current_time - self._period_in_seconds
                ):
                    self._rate_queue.popleft()
                    self._token_queue.popleft()

                # If sliding window still exceed request limit, wait again
                # Waiting requires reacquiring the lock, allowing other threads
                # to see if their request fits within the rate limiting windows
                # Makes more sense for token limit than request limit
                if (
                    self._rpp is not None
                    and self._rpp > 0
                    and len(self._rate_queue) >= self._rpp
                ):
                    continue

                # Check if current token window exceeds token limit
                # If it does, wait again
                # This does not account for the tokens from the current request
                # This is intentional, as we want to allow the current request
                # to be processed if it is larger than the tpm but smaller than context window.
                # tpm is a rate/soft limit and not the hard limit of context window limits.
                if (
                    self._tpp is not None
                    and self._tpp > 0
                    and sum(self._token_queue) >= self._tpp
                ):
                    continue

                # This check accounts for the current request token usage
                # is within the token limits bound.
                # If the current requests tokens exceeds the token limit,
                # Then let it be processed.
                if (
                    self._tpp is not None
                    and self._tpp > 0
                    and token_count <= self._tpp
                    and sum(self._token_queue) + token_count > self._tpp
                ):
                    continue

                # If there was a previous call, check if we need to stagger
                if (
                    self._stagger > 0
                    and (
                        self._last_time  # is None if this is the first hit to the rate limiter
                        and current_time - self._last_time
                        < self._stagger  # If more time has passed than the stagger time, we can proceed
                    )
                ):
                    time.sleep(self._stagger - (current_time - self._last_time))
                    current_time = time.time()

                # Add the current request to the sliding window
                self._rate_queue.append(current_time)
                self._token_queue.append(token_count)
                self._last_time = current_time
                break
        yield
