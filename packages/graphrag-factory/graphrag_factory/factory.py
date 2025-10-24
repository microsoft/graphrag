# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""Factory ABC."""

from abc import ABC
from collections.abc import Callable
from typing import Any, ClassVar, Generic, Literal, TypeVar

T = TypeVar("T", covariant=True)

ServiceScope = Literal["singleton", "transient"]


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
            self._service_initializers: dict[
                str, tuple[ServiceScope, Callable[..., T]]
            ] = {}
            self._initialized_services: dict[str, T] = {}
            self._initialized = True

    def __contains__(self, strategy: str) -> bool:
        """Check if a strategy is registered."""
        return strategy in self._service_initializers

    def keys(self) -> list[str]:
        """Get a list of registered strategy names."""
        return list(self._service_initializers.keys())

    def register(
        self,
        strategy: str,
        initializer: Callable[..., T],
        scope: ServiceScope = "transient",
    ) -> None:
        """
        Register a new service.

        Args
        ----
            strategy: The name of the strategy.
            initializer: A callable that creates an instance of T.
            scope: The service scope, either 'singleton' or 'transient'.
        """
        self._service_initializers[strategy] = (scope, initializer)

    def create(self, strategy: str, init_args: dict[str, Any] | None = None) -> T:
        """
        Create a service instance based on the strategy.

        Args
        ----
            strategy: The name of the strategy.
            init_args: Dict of keyword arguments to pass to the service initializer.

        Returns
        -------
            An instance of T.

        Raises
        ------
            ValueError: If the strategy is not registered.
        """
        if strategy not in self._service_initializers:
            msg = f"Strategy '{strategy}' is not registered."
            raise ValueError(msg)

        scope, service_initializer = self._service_initializers[strategy]
        if scope == "singleton":
            if strategy not in self._initialized_services:
                self._initialized_services[strategy] = service_initializer(
                    **(init_args or {})
                )
            return self._initialized_services[strategy]

        return service_initializer(**(init_args or {}))
