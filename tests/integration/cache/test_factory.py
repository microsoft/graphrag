# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
"""CacheFactory Tests.

These tests will test the CacheFactory() class and the creation of each cache type that is natively supported.
"""

import sys

import pytest
from graphrag_cache import Cache, CacheConfig, CacheType, create_cache, register_cache
from graphrag_cache.cache_factory import cache_factory
from graphrag_cache.json_cache import JsonCache
from graphrag_cache.memory_cache import MemoryCache
from graphrag_cache.noop_cache import NoopCache
from graphrag_storage import StorageConfig, StorageType, create_storage

# cspell:disable-next-line well-known-key
WELL_KNOWN_BLOB_STORAGE_KEY = "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
# cspell:disable-next-line well-known-key
WELL_KNOWN_COSMOS_CONNECTION_STRING = "AccountEndpoint=https://127.0.0.1:8081/;AccountKey=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="


def test_create_noop_cache():
    cache = create_cache(
        CacheConfig(
            type=CacheType.Noop,
        )
    )
    assert isinstance(cache, NoopCache)


def test_create_memory_cache():
    cache = create_cache(
        CacheConfig(
            type=CacheType.Memory,
        )
    )
    assert isinstance(cache, MemoryCache)


def test_create_file_cache():
    storage = create_storage(
        StorageConfig(
            type=StorageType.Memory,
        )
    )
    cache = create_cache(
        CacheConfig(
            type=CacheType.Json,
        ),
        storage=storage,
    )
    assert isinstance(cache, JsonCache)


def test_create_blob_cache():
    storage = create_storage(
        StorageConfig(
            type=StorageType.AzureBlob,
            connection_string=WELL_KNOWN_BLOB_STORAGE_KEY,
            container_name="testcontainer",
            base_dir="testcache",
        )
    )
    cache = create_cache(
        CacheConfig(
            type=CacheType.Json,
        ),
        storage=storage,
    )

    assert isinstance(cache, JsonCache)


@pytest.mark.skipif(
    not sys.platform.startswith("win"),
    reason="cosmosdb emulator is only available on windows runners at this time",
)
def test_create_cosmosdb_cache():
    storage = create_storage(
        StorageConfig(
            type=StorageType.AzureCosmos,
            connection_string=WELL_KNOWN_COSMOS_CONNECTION_STRING,
            database_name="testdatabase",
            container_name="testcontainer",
        )
    )
    cache = create_cache(
        CacheConfig(
            type=CacheType.Json,
        ),
        storage=storage,
    )
    assert isinstance(cache, JsonCache)


def test_register_and_create_custom_cache():
    """Test registering and creating a custom cache type."""
    from unittest.mock import MagicMock

    # Create a mock that satisfies the PipelineCache interface
    custom_cache_class = MagicMock(spec=Cache)
    # Make the mock return a mock instance when instantiated
    instance = MagicMock()
    instance.initialized = True
    custom_cache_class.return_value = instance

    register_cache("custom", lambda **kwargs: custom_cache_class(**kwargs))
    cache = create_cache(CacheConfig(type="custom"))

    assert custom_cache_class.called
    assert cache is instance
    # Access the attribute we set on our mock
    assert cache.initialized is True  # type: ignore # Attribute only exists on our mock

    # Check if it's in the list of registered cache types
    assert "custom" in cache_factory


def test_create_unknown_cache():
    with pytest.raises(
        ValueError,
        match="CacheConfig\\.type 'unknown' is not registered in the CacheFactory\\.",
    ):
        create_cache(CacheConfig(type="unknown"))


def test_register_class_directly_works():
    """Test that registering a class directly works (CacheFactory() allows this)."""

    class CustomCache(Cache):
        def __init__(self, **kwargs):
            pass

        async def get(self, key: str):
            return None

        async def set(self, key: str, value, debug_data=None):
            pass

        async def has(self, key: str):
            return False

        async def delete(self, key: str):
            pass

        async def clear(self):
            pass

        def child(self, name: str):
            return self

    # CacheFactory() allows registering classes directly (no TypeError)
    register_cache("custom_class", CustomCache)

    # Verify it was registered
    assert "custom_class" in cache_factory

    # Test creating an instance
    cache = create_cache(CacheConfig(type="custom_class"))
    assert isinstance(cache, CustomCache)
