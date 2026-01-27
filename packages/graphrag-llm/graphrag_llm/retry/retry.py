# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Retry abstract base class."""

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any


class Retry(ABC):
    """Retry Abstract Base Class."""

    @abstractmethod
    def __init__(self, /, **kwargs: Any):
        """Initialize Retry."""
        raise NotImplementedError

    @abstractmethod
    def retry(self, *, func: Callable[..., Any], input_args: dict[str, Any]) -> Any:
        """Retry a synchronous function."""
        raise NotImplementedError

    @abstractmethod
    async def retry_async(
        self,
        *,
        func: Callable[..., Awaitable[Any]],
        input_args: dict[str, Any],
    ) -> Any:
        """Retry an asynchronous function."""
        raise NotImplementedError
