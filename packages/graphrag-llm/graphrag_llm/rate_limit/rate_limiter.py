# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""LiteLLM Rate Limiter."""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any


class RateLimiter(ABC):
    """Abstract base class for rate limiters."""

    @abstractmethod
    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        """Initialize the Rate Limiter."""
        raise NotImplementedError

    @abstractmethod
    @contextmanager
    def acquire(self, token_count: int) -> Iterator[None]:
        """
        Acquire Rate Limiter.

        Args
        ----
            token_count: int
                The estimated number of prompt and response tokens for the current request.

        Yields
        ------
            None: This context manager does not return any value.
        """
        raise NotImplementedError
