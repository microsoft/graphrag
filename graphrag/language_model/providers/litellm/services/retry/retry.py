# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""LiteLLM Retry Abstract Base Class."""

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any


class Retry(ABC):
    """LiteLLM Retry Abstract Base Class."""

    @abstractmethod
    def __init__(self, /, **kwargs: Any):
        msg = "Retry subclasses must implement the __init__ method."
        raise NotImplementedError(msg)

    @abstractmethod
    def retry(self, func: Callable[..., Any], **kwargs: Any) -> Any:
        """Retry a synchronous function."""
        msg = "Subclasses must implement this method"
        raise NotImplementedError(msg)

    @abstractmethod
    async def aretry(
        self,
        func: Callable[..., Awaitable[Any]],
        **kwargs: Any,
    ) -> Any:
        """Retry an asynchronous function."""
        msg = "Subclasses must implement this method"
        raise NotImplementedError(msg)
