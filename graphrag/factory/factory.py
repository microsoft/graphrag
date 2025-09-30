# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""Factory ABC."""

from abc import ABC
from collections.abc import Callable
from typing import Any, ClassVar, Generic, TypeVar

T = TypeVar("T", covariant=True)


class Factory(ABC, Generic[T]):
    """Abstract base class for factories."""

    _instance: ClassVar["Factory | None"] = None

    def __new__(cls, *args: Any, **kwargs: Any) -> "Factory":
        """Create a new instance of Factory if it does not exist."""
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._services: dict[str, Callable[..., T]] = {}
            self._initialized = True

    def __contains__(self, strategy: str) -> bool:
        """Check if a strategy is registered."""
        return strategy in self._services

    def keys(self) -> list[str]:
        """Get a list of registered strategy names."""
        return list(self._services.keys())

    def register(self, *, strategy: str, service_initializer: Callable[..., T]) -> None:
        """
        Register a new service.

        Args
        ----
            strategy: The name of the strategy.
            service_initializer: A callable that creates an instance of T.
        """
        self._services[strategy] = service_initializer

    def create(self, *, strategy: str, **kwargs: Any) -> T:
        """
        Create a service instance based on the strategy.

        Args
        ----
            strategy: The name of the strategy.
            **kwargs: Additional arguments to pass to the service initializer.

        Returns
        -------
            An instance of T.

        Raises
        ------
            ValueError: If the strategy is not registered.
        """
        if strategy not in self._services:
            msg = f"Strategy '{strategy}' is not registered."
            raise ValueError(msg)
        return self._services[strategy](**kwargs)
