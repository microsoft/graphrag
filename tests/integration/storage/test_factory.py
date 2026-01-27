# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
"""StorageFactory Tests.

These tests will test the StorageFactory class and the creation of each storage type that is natively supported.
"""

import sys

import pytest
from graphrag_storage import (
    Storage,
    StorageConfig,
    StorageType,
    create_storage,
    register_storage,
)
from graphrag_storage.azure_blob_storage import AzureBlobStorage
from graphrag_storage.azure_cosmos_storage import AzureCosmosStorage
from graphrag_storage.file_storage import FileStorage
from graphrag_storage.memory_storage import MemoryStorage

# cspell:disable-next-line well-known-key
WELL_KNOWN_BLOB_STORAGE_KEY = "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
# cspell:disable-next-line well-known-key
WELL_KNOWN_COSMOS_CONNECTION_STRING = "AccountEndpoint=https://127.0.0.1:8081/;AccountKey=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="


@pytest.mark.skip(reason="Blob storage emulator is not available in this environment")
def test_create_blob_storage():
    config = StorageConfig(
        type=StorageType.AzureBlob,
        connection_string=WELL_KNOWN_BLOB_STORAGE_KEY,
        base_dir="testbasedir",
        container_name="testcontainer",
    )
    storage = create_storage(config)
    assert isinstance(storage, AzureBlobStorage)


@pytest.mark.skipif(
    not sys.platform.startswith("win"),
    reason="cosmosdb emulator is only available on windows runners at this time",
)
def test_create_cosmosdb_storage():
    config = StorageConfig(
        type=StorageType.AzureCosmos,
        connection_string=WELL_KNOWN_COSMOS_CONNECTION_STRING,
        database_name="testdatabase",
        container_name="testcontainer",
    )
    storage = create_storage(config)
    assert isinstance(storage, AzureCosmosStorage)


def test_create_file():
    config = StorageConfig(
        type=StorageType.File,
        base_dir="/tmp/teststorage",
    )
    storage = create_storage(config)
    assert isinstance(storage, FileStorage)


def test_create_memory_storage():
    config = StorageConfig(
        base_dir="",
        type=StorageType.Memory,
    )
    storage = create_storage(config)
    assert isinstance(storage, MemoryStorage)


def test_register_and_create_custom_storage():
    """Test registering and creating a custom storage type."""
    from unittest.mock import MagicMock

    # Create a mock that satisfies the Storage interface
    custom_storage_class = MagicMock(spec=Storage)
    # Make the mock return a mock instance when instantiated
    instance = MagicMock()
    # We can set attributes on the mock instance, even if they don't exist on Storage
    instance.initialized = True
    custom_storage_class.return_value = instance

    register_storage("custom", lambda **kwargs: custom_storage_class(**kwargs))
    storage = create_storage(StorageConfig(type="custom"))

    assert custom_storage_class.called
    assert storage is instance
    # Access the attribute we set on our mock
    assert storage.initialized is True  # type: ignore # Attribute only exists on our mock


def test_create_unknown_storage():
    with pytest.raises(
        ValueError,
        match="StorageConfig\\.type 'unknown' is not registered in the StorageFactory\\.",
    ):
        create_storage(StorageConfig(type="unknown"))


def test_register_class_directly_works():
    """Test that registering a class directly works (StorageFactory allows this)."""
    import re
    from collections.abc import Iterator
    from typing import Any

    class CustomStorage(Storage):
        def __init__(self, **kwargs):
            pass

        def find(
            self,
            file_pattern: re.Pattern[str],
        ) -> Iterator[str]:
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

        def child(self, name: str | None) -> "Storage":
            return self

        def keys(self) -> list[str]:
            return []

        async def get_creation_date(self, key: str) -> str:
            return "2024-01-01 00:00:00 +0000"

    # StorageFactory allows registering classes directly (no TypeError)
    register_storage("custom_class", CustomStorage)

    # Test creating an instance
    storage = create_storage(StorageConfig(type="custom_class"))
    assert isinstance(storage, CustomStorage)
