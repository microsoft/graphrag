# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License


"""Cache factory implementation."""

from collections.abc import Callable

from graphrag_common.factory import Factory, ServiceScope
from graphrag_storage import Storage, create_storage

from graphrag_cache.cache import Cache
from graphrag_cache.cache_config import CacheConfig
from graphrag_cache.cache_type import CacheType


class CacheFactory(Factory["Cache"]):
    """A factory class for cache implementations."""


cache_factory = CacheFactory()


def register_cache(
    cache_type: str,
    cache_initializer: Callable[..., Cache],
    scope: ServiceScope = "transient",
) -> None:
    """Register a custom cache implementation.

    Args
    ----
        - cache_type: str
            The cache id to register.
        - cache_initializer: Callable[..., Cache]
            The cache initializer to register.
    """
    cache_factory.register(cache_type, cache_initializer, scope)


def create_cache(
    config: CacheConfig | None = None, storage: Storage | None = None
) -> "Cache":
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
    config = config or CacheConfig()
    config_model = config.model_dump()
    cache_strategy = config.type

    if not storage and config.storage:
        storage = create_storage(config.storage)

    if cache_strategy not in cache_factory:
        match cache_strategy:
            case CacheType.Json:
                from graphrag_cache.json_cache import JsonCache

                register_cache(CacheType.Json, JsonCache)

            case CacheType.Memory:
                from graphrag_cache.memory_cache import MemoryCache

                register_cache(CacheType.Memory, MemoryCache)

            case CacheType.Noop:
                from graphrag_cache.noop_cache import NoopCache

                register_cache(CacheType.Noop, NoopCache)

            case _:
                msg = f"CacheConfig.type '{cache_strategy}' is not registered in the CacheFactory. Registered types: {', '.join(cache_factory.keys())}."
                raise ValueError(msg)

    if storage:
        config_model["storage"] = storage

    return cache_factory.create(strategy=cache_strategy, init_args=config_model)
