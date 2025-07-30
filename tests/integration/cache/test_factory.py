# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
"""CacheFactory Tests.

These tests will test the CacheFactory class and the creation of each cache type that is natively supported.
"""

import pytest

from graphrag.cache.factory import CacheFactory
from graphrag.cache.json_pipeline_cache import JsonPipelineCache
from graphrag.cache.memory_pipeline_cache import InMemoryCache
from graphrag.cache.noop_pipeline_cache import NoopPipelineCache
from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.config.enums import CacheType


def test_create_noop_cache():
    kwargs = {}
    cache = CacheFactory.create_cache(CacheType.none, "/tmp", kwargs)
    assert isinstance(cache, NoopPipelineCache)


def test_create_memory_cache():
    kwargs = {}
    cache = CacheFactory.create_cache(CacheType.memory, "/tmp", kwargs)
    assert isinstance(cache, InMemoryCache)


def test_create_file_cache():
    kwargs = {"base_dir": "testcache"}
    cache = CacheFactory.create_cache(CacheType.file, "/tmp", kwargs)
    assert isinstance(cache, JsonPipelineCache)


@pytest.mark.skip(reason="Blob storage emulator is not available in this environment")
def test_create_blob_cache():
    # cspell:disable-next-line well-known-key
    well_known_blob_storage_key = "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
    kwargs = {
        "connection_string": well_known_blob_storage_key,
        "container_name": "testcontainer",
        "base_dir": "testcache",
    }
    cache = CacheFactory.create_cache(CacheType.blob, "/tmp", kwargs)
    assert isinstance(cache, JsonPipelineCache)


@pytest.mark.skip(reason="CosmosDB emulator is not available in this environment")
def test_create_cosmosdb_cache():
    # cspell:disable-next-line well-known-key
    well_known_cosmos_connection_string = "AccountEndpoint=https://127.0.0.1:8081/;AccountKey=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="
    kwargs = {
        "connection_string": well_known_cosmos_connection_string,
        "database_name": "testdatabase",
        "container_name": "testcontainer",
    }
    cache = CacheFactory.create_cache(CacheType.cosmosdb, "/tmp", kwargs)
    assert isinstance(cache, JsonPipelineCache)


def test_create_none_cache_with_none_type():
    """Test creating cache with None cache type returns NoopPipelineCache."""
    cache = CacheFactory.create_cache(None, "/tmp", {})
    assert isinstance(cache, NoopPipelineCache)


def test_register_and_create_custom_cache():
    """Test registering and creating a custom cache type."""
    from unittest.mock import MagicMock

    # Create a mock that satisfies the PipelineCache interface
    custom_cache_class = MagicMock(spec=PipelineCache)
    # Make the mock return a mock instance when instantiated
    instance = MagicMock()
    instance.initialized = True
    custom_cache_class.return_value = instance

    CacheFactory.register("custom", lambda **kwargs: custom_cache_class(**kwargs))
    cache = CacheFactory.create_cache("custom", "/tmp", {})

    assert custom_cache_class.called
    assert cache is instance
    # Access the attribute we set on our mock
    assert cache.initialized is True  # type: ignore # Attribute only exists on our mock

    # Check if it's in the list of registered cache types
    assert "custom" in CacheFactory.get_cache_types()
    assert CacheFactory.is_supported_type("custom")


def test_get_cache_types():
    cache_types = CacheFactory.get_cache_types()
    # Check that built-in types are registered
    assert CacheType.none.value in cache_types
    assert CacheType.memory.value in cache_types
    assert CacheType.file.value in cache_types
    assert CacheType.blob.value in cache_types
    assert CacheType.cosmosdb.value in cache_types


def test_create_unknown_cache():
    with pytest.raises(ValueError, match="Unknown cache type: unknown"):
        CacheFactory.create_cache("unknown", "/tmp", {})


def test_is_supported_type():
    # Test built-in types
    assert CacheFactory.is_supported_type(CacheType.none.value)
    assert CacheFactory.is_supported_type(CacheType.memory.value)
    assert CacheFactory.is_supported_type(CacheType.file.value)
    assert CacheFactory.is_supported_type(CacheType.blob.value)
    assert CacheFactory.is_supported_type(CacheType.cosmosdb.value)

    # Test unknown type
    assert not CacheFactory.is_supported_type("unknown")


def test_enum_and_string_compatibility():
    """Test that both enum and string types work for cache creation."""
    kwargs = {}

    # Test with enum
    cache_enum = CacheFactory.create_cache(CacheType.memory, "/tmp", kwargs)
    assert isinstance(cache_enum, InMemoryCache)

    # Test with string
    cache_str = CacheFactory.create_cache("memory", "/tmp", kwargs)
    assert isinstance(cache_str, InMemoryCache)

    # Both should create the same type
    assert type(cache_enum) is type(cache_str)


def test_register_class_directly_raises_error():
    """Test that registering a class directly raises a TypeError."""
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

    # Attempting to register a class directly should raise TypeError
    with pytest.raises(
        TypeError, match="Registering classes directly is no longer supported"
    ):
        CacheFactory.register("custom_class", CustomCache)
