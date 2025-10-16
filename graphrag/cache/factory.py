# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Factory functions for creating a cache."""

from __future__ import annotations

from graphrag.cache.json_pipeline_cache import JsonPipelineCache
from graphrag.cache.memory_pipeline_cache import InMemoryCache
from graphrag.cache.noop_pipeline_cache import NoopPipelineCache
from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.config.enums import CacheType
from graphrag.factory.factory import Factory
from graphrag.storage.blob_pipeline_storage import BlobPipelineStorage
from graphrag.storage.cosmosdb_pipeline_storage import CosmosDBPipelineStorage
from graphrag.storage.file_pipeline_storage import FilePipelineStorage


class CacheFactory(Factory[PipelineCache]):
    """A factory class for cache implementations.

    Includes a method for users to register a custom cache implementation.

    Configuration arguments are passed to each cache implementation as kwargs
    for individual enforcement of required/optional arguments.
    """


# --- register built-in cache implementations ---
def create_file_cache(root_dir: str, base_dir: str, **kwargs) -> PipelineCache:
    """Create a file-based cache implementation."""
    # Create storage with base_dir in kwargs since FilePipelineStorage expects it there
    storage_kwargs = {"base_dir": root_dir, **kwargs}
    storage = FilePipelineStorage(**storage_kwargs).child(base_dir)
    return JsonPipelineCache(storage)


def create_blob_cache(**kwargs) -> PipelineCache:
    """Create a blob storage-based cache implementation."""
    storage = BlobPipelineStorage(**kwargs)
    return JsonPipelineCache(storage)


def create_cosmosdb_cache(**kwargs) -> PipelineCache:
    """Create a CosmosDB-based cache implementation."""
    storage = CosmosDBPipelineStorage(**kwargs)
    return JsonPipelineCache(storage)


def create_noop_cache(**_kwargs) -> PipelineCache:
    """Create a no-op cache implementation."""
    return NoopPipelineCache()


def create_memory_cache(**kwargs) -> PipelineCache:
    """Create a memory cache implementation."""
    return InMemoryCache(**kwargs)


# --- register built-in cache implementations ---
cache_factory = CacheFactory()
cache_factory.register(CacheType.none.value, create_noop_cache)
cache_factory.register(CacheType.memory.value, create_memory_cache)
cache_factory.register(CacheType.file.value, create_file_cache)
cache_factory.register(CacheType.blob.value, create_blob_cache)
cache_factory.register(CacheType.cosmosdb.value, create_cosmosdb_cache)
