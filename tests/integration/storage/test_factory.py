# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
"""StorageFactory Tests.

These tests will test the StorageFactory class and the creation of each storage type that is natively supported.
"""

import sys

import pytest

from graphrag.config.enums import StorageType
from graphrag.storage.blob_pipeline_storage import BlobPipelineStorage
from graphrag.storage.cosmosdb_pipeline_storage import CosmosDBPipelineStorage
from graphrag.storage.factory import StorageFactory
from graphrag.storage.file_pipeline_storage import FilePipelineStorage
from graphrag.storage.memory_pipeline_storage import MemoryPipelineStorage
from graphrag.storage.pipeline_storage import PipelineStorage

# cspell:disable-next-line well-known-key
WELL_KNOWN_BLOB_STORAGE_KEY = "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
# cspell:disable-next-line well-known-key
WELL_KNOWN_COSMOS_CONNECTION_STRING = "AccountEndpoint=https://127.0.0.1:8081/;AccountKey=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="


@pytest.mark.skip(reason="Blob storage emulator is not available in this environment")
def test_create_blob_storage():
    kwargs = {
        "type": "blob",
        "connection_string": WELL_KNOWN_BLOB_STORAGE_KEY,
        "base_dir": "testbasedir",
        "container_name": "testcontainer",
    }
    storage = StorageFactory.create_storage(StorageType.blob.value, kwargs)
    assert isinstance(storage, BlobPipelineStorage)


@pytest.mark.skipif(
    not sys.platform.startswith("win"),
    reason="cosmosdb emulator is only available on windows runners at this time",
)
def test_create_cosmosdb_storage():
    kwargs = {
        "type": "cosmosdb",
        "connection_string": WELL_KNOWN_COSMOS_CONNECTION_STRING,
        "base_dir": "testdatabase",
        "container_name": "testcontainer",
    }
    storage = StorageFactory.create_storage(StorageType.cosmosdb.value, kwargs)
    assert isinstance(storage, CosmosDBPipelineStorage)


def test_create_file_storage():
    kwargs = {"type": "file", "base_dir": "/tmp/teststorage"}
    storage = StorageFactory.create_storage(StorageType.file.value, kwargs)
    assert isinstance(storage, FilePipelineStorage)


def test_create_memory_storage():
    kwargs = {}  # MemoryPipelineStorage doesn't accept any constructor parameters
    storage = StorageFactory.create_storage(StorageType.memory.value, kwargs)
    assert isinstance(storage, MemoryPipelineStorage)


def test_register_and_create_custom_storage():
    """Test registering and creating a custom storage type."""
    from unittest.mock import MagicMock

    # Create a mock that satisfies the PipelineStorage interface
    custom_storage_class = MagicMock(spec=PipelineStorage)
    # Make the mock return a mock instance when instantiated
    instance = MagicMock()
    # We can set attributes on the mock instance, even if they don't exist on PipelineStorage
    instance.initialized = True
    custom_storage_class.return_value = instance

    StorageFactory.register("custom", lambda **kwargs: custom_storage_class(**kwargs))
    storage = StorageFactory.create_storage("custom", {})

    assert custom_storage_class.called
    assert storage is instance
    # Access the attribute we set on our mock
    assert storage.initialized is True  # type: ignore # Attribute only exists on our mock

    # Check if it's in the list of registered storage types
    assert "custom" in StorageFactory.get_storage_types()
    assert StorageFactory.is_supported_type("custom")


def test_get_storage_types():
    storage_types = StorageFactory.get_storage_types()
    # Check that built-in types are registered
    assert StorageType.file.value in storage_types
    assert StorageType.memory.value in storage_types
    assert StorageType.blob.value in storage_types
    assert StorageType.cosmosdb.value in storage_types


def test_create_unknown_storage():
    with pytest.raises(ValueError, match="Unknown storage type: unknown"):
        StorageFactory.create_storage("unknown", {})


def test_register_class_directly_works():
    """Test that registering a class directly works (StorageFactory allows this)."""
    import re
    from collections.abc import Iterator
    from typing import Any

    from graphrag.storage.pipeline_storage import PipelineStorage

    class CustomStorage(PipelineStorage):
        def __init__(self, **kwargs):
            pass

        def find(
            self,
            file_pattern: re.Pattern[str],
            base_dir: str | None = None,
            file_filter: dict[str, Any] | None = None,
            max_count=-1,
        ) -> Iterator[tuple[str, dict[str, Any]]]:
            return iter([])

        async def get(
            self, key: str, as_bytes: bool | None = None, encoding: str | None = None
        ) -> Any:
            return None

        async def set(self, key: str, value: Any, encoding: str | None = None) -> None:
            pass

        async def delete(self, key: str) -> None:
            pass

        async def has(self, key: str) -> bool:
            return False

        async def clear(self) -> None:
            pass

        def child(self, name: str | None) -> "PipelineStorage":
            return self

        def keys(self) -> list[str]:
            return []

        async def get_creation_date(self, key: str) -> str:
            return "2024-01-01 00:00:00 +0000"

    # StorageFactory allows registering classes directly (no TypeError)
    StorageFactory.register("custom_class", CustomStorage)

    # Verify it was registered
    assert "custom_class" in StorageFactory.get_storage_types()
    assert StorageFactory.is_supported_type("custom_class")

    # Test creating an instance
    storage = StorageFactory.create_storage("custom_class", {})
    assert isinstance(storage, CustomStorage)
