# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""Factory ABC."""

from abc import ABC
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, ClassVar, Generic, Literal, TypeVar

from graphrag_common.hasher import hash_data

T = TypeVar("T", covariant=True)

ServiceScope = Literal["singleton", "transient"]


@dataclass
class _ServiceDescriptor(Generic[T]):
    """Descriptor for a service."""

    scope: ServiceScope
    initializer: Callable[..., T]


class Factory(ABC, Generic[T]):
    """Abstract base class for factories."""

    _instance: ClassVar["Factory | None"] = None

    def __new__(cls, *args: Any, **kwargs: Any) -> "Factory[T]":
        """Create a new instance of Factory if it does not exist."""
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._service_initializers: dict[str, _ServiceDescriptor[T]] = {}
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
            strategy: str
                The name of the strategy.
            initializer: Callable[..., T]
                A callable that creates an instance of T.
            scope: ServiceScope (default: "transient")
                The scope of the service ("singleton" or "transient").
                Singleton services are cached based on their init args
                so that the same instance is returned for the same init args.
        """
        self._service_initializers[strategy] = _ServiceDescriptor(scope, initializer)

    def create(self, strategy: str, init_args: dict[str, Any] | None = None) -> T:
        """
        Create a service instance based on the strategy.

        Args
        ----
            strategy: str
                The name of the strategy.
            init_args: dict[str, Any] | None
                A dictionary of keyword arguments to pass to the service initializer.

        Returns
        -------
            An instance of T.

        Raises
        ------
            ValueError: If the strategy is not registered.
        """
        if strategy not in self._service_initializers:
            msg = f"Strategy '{strategy}' is not registered. Registered strategies are: {', '.join(list(self._service_initializers.keys()))}"
            raise ValueError(msg)

        # Delete entries with value None
        # That way services can have default values
        init_args = {k: v for k, v in (init_args or {}).items() if v is not None}

        service_descriptor = self._service_initializers[strategy]
        if service_descriptor.scope == "singleton":
            cache_key = hash_data({
                "strategy": strategy,
                "init_args": init_args,
            })

            if cache_key not in self._initialized_services:
                self._initialized_services[cache_key] = service_descriptor.initializer(
                    **init_args
                )
            return self._initialized_services[cache_key]

        return service_descriptor.initializer(**(init_args or {}))
