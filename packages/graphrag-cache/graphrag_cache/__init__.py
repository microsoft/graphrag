# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The GraphRAG Cache package."""

from graphrag_cache.cache import Cache
from graphrag_cache.cache_config import CacheConfig
from graphrag_cache.cache_factory import create_cache, register_cache
from graphrag_cache.cache_key import CacheKeyCreator, create_cache_key
from graphrag_cache.cache_type import CacheType

__all__ = [
    "Cache",
    "CacheConfig",
    "CacheKeyCreator",
    "CacheType",
    "create_cache",
    "create_cache_key",
    "register_cache",
]
