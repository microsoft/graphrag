# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License


"""Cache factory implementation."""

from collections.abc import Callable

from graphrag_common.factory import Factory, ServiceScope
from graphrag_storage import Storage

from graphrag_cache.cache import Cache
from graphrag_cache.cache_config import CacheConfig
from graphrag_cache.cache_type import CacheType


class CacheFactory(Factory[Cache]):
    """A factory class for cache implementations."""


cache_factory = CacheFactory()


def register_cache(
    cache_type: str,
    cache_initializer: Callable[..., Cache],
    scope: ServiceScope = "transient",
) -> None:
    """Register a custom storage implementation.

    Args
    ----
        - storage_type: str
            The storage id to register.
        - storage_initializer: Callable[..., Storage]
            The storage initializer to register.
    """
    cache_factory.register(cache_type, cache_initializer, scope)


def create_cache(config: CacheConfig, storage: Storage | None = None) -> Cache:
    """Create a cache implementation based on the given configuration.

    Args
    ----
        - config: CacheConfig
            The cache configuration to use.
        - storage: Storage | None
            The storage implementation to use for file-based caches such as 'Json'.

    Returns
    -------
        Cache
            The created cache implementation.
    """
    config_model = config.model_dump()
    cache_strategy = config.type

    if cache_strategy not in cache_factory:
        match cache_strategy:
            case "json":
                from graphrag_cache.json_cache import JsonCache

                register_cache(CacheType.Json, JsonCache)

            case "memory":
                from graphrag_cache.memory_cache import MemoryCache

                register_cache(CacheType.Memory, MemoryCache)

            case "noop":
                from graphrag_cache.noop_cache import NoopCache

                register_cache(CacheType.Noop, NoopCache)

            case _:
                msg = f"CacheConfig.type '{cache_strategy}' is not registered in the CacheFactory. Registered types: {', '.join(cache_factory.keys())}."
                raise ValueError(msg)

    return cache_factory.create(
        strategy=cache_strategy, init_args={"storage": storage, **config_model}
    )
