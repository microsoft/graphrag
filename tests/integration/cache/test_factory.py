# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
"""CacheFactory Tests.

These tests will test the CacheFactory() class and the creation of each cache type that is natively supported.
"""

import sys

import pytest
from graphrag.cache.factory import CacheFactory
from graphrag.cache.json_pipeline_cache import JsonPipelineCache
from graphrag.cache.memory_pipeline_cache import InMemoryCache
from graphrag.cache.noop_pipeline_cache import NoopPipelineCache
from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.config.enums import CacheType

# cspell:disable-next-line well-known-key
WELL_KNOWN_BLOB_STORAGE_KEY = "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
# cspell:disable-next-line well-known-key
WELL_KNOWN_COSMOS_CONNECTION_STRING = "AccountEndpoint=https://127.0.0.1:8081/;AccountKey=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="


def test_create_noop_cache():
    cache = CacheFactory().create(strategy=CacheType.none.value)
    assert isinstance(cache, NoopPipelineCache)


def test_create_memory_cache():
    cache = CacheFactory().create(strategy=CacheType.memory.value)
    assert isinstance(cache, InMemoryCache)


def test_create_file_cache():
    cache = CacheFactory().create(
        strategy=CacheType.file.value,
        init_args={"root_dir": "/tmp", "base_dir": "testcache"},
    )
    assert isinstance(cache, JsonPipelineCache)


def test_create_blob_cache():
    init_args = {
        "connection_string": WELL_KNOWN_BLOB_STORAGE_KEY,
        "container_name": "testcontainer",
        "base_dir": "testcache",
    }
    cache = CacheFactory().create(strategy=CacheType.blob.value, init_args=init_args)
    assert isinstance(cache, JsonPipelineCache)


@pytest.mark.skipif(
    not sys.platform.startswith("win"),
    reason="cosmosdb emulator is only available on windows runners at this time",
)
def test_create_cosmosdb_cache():
    init_args = {
        "connection_string": WELL_KNOWN_COSMOS_CONNECTION_STRING,
        "base_dir": "testdatabase",
        "container_name": "testcontainer",
    }
    cache = CacheFactory().create(
        strategy=CacheType.cosmosdb.value, init_args=init_args
    )
    assert isinstance(cache, JsonPipelineCache)


def test_register_and_create_custom_cache():
    """Test registering and creating a custom cache type."""
    from unittest.mock import MagicMock

    # Create a mock that satisfies the PipelineCache interface
    custom_cache_class = MagicMock(spec=PipelineCache)
    # Make the mock return a mock instance when instantiated
    instance = MagicMock()
    instance.initialized = True
    custom_cache_class.return_value = instance

    CacheFactory().register(
        strategy="custom",
        initializer=lambda **kwargs: custom_cache_class(**kwargs),
    )
    cache = CacheFactory().create(strategy="custom")

    assert custom_cache_class.called
    assert cache is instance
    # Access the attribute we set on our mock
    assert cache.initialized is True  # type: ignore # Attribute only exists on our mock

    # Check if it's in the list of registered cache types
    assert "custom" in CacheFactory()


def test_create_unknown_cache():
    with pytest.raises(ValueError, match="Strategy 'unknown' is not registered\\."):
        CacheFactory().create(strategy="unknown")


def test_is_supported_type():
    # Test built-in types
    assert CacheType.none.value in CacheFactory()
    assert CacheType.memory.value in CacheFactory()
    assert CacheType.file.value in CacheFactory()
    assert CacheType.blob.value in CacheFactory()
    assert CacheType.cosmosdb.value in CacheFactory()

    # Test unknown type
    assert "unknown" not in CacheFactory()


def test_enum_and_string_compatibility():
    """Test that both enum and string types work for cache creation."""
    # Test with enum
    cache_enum = CacheFactory().create(strategy=CacheType.memory)
    assert isinstance(cache_enum, InMemoryCache)

    # Test with string
    cache_str = CacheFactory().create(strategy="memory")
    assert isinstance(cache_str, InMemoryCache)

    # Both should create the same type
    assert type(cache_enum) is type(cache_str)


def test_register_class_directly_works():
    """Test that registering a class directly works (CacheFactory() allows this)."""
    from graphrag.cache.pipeline_cache import PipelineCache

    class CustomCache(PipelineCache):
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
    CacheFactory().register("custom_class", CustomCache)

    # Verify it was registered
    assert "custom_class" in CacheFactory()

    # Test creating an instance
    cache = CacheFactory().create(strategy="custom_class")
    assert isinstance(cache, CustomCache)
