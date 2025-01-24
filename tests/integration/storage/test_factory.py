# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
"""StorageFactory Tests.

These tests will test the StorageFactory class and the creation of each storage type that is natively supported.
"""

import sys

import pytest

from graphrag.config.enums import OutputType
from graphrag.storage.blob_pipeline_storage import BlobPipelineStorage
from graphrag.storage.cosmosdb_pipeline_storage import CosmosDBPipelineStorage
from graphrag.storage.factory import StorageFactory
from graphrag.storage.file_pipeline_storage import FilePipelineStorage
from graphrag.storage.memory_pipeline_storage import MemoryPipelineStorage

# cspell:disable-next-line well-known-key
WELL_KNOWN_BLOB_STORAGE_KEY = "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
# cspell:disable-next-line well-known-key
WELL_KNOWN_COSMOS_CONNECTION_STRING = "AccountEndpoint=https://127.0.0.1:8081/;AccountKey=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="


def test_create_blob_storage():
    kwargs = {
        "type": "blob",
        "connection_string": WELL_KNOWN_BLOB_STORAGE_KEY,
        "base_dir": "testbasedir",
        "container_name": "testcontainer",
    }
    storage = StorageFactory.create_storage(OutputType.blob, kwargs)
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
    storage = StorageFactory.create_storage(OutputType.cosmosdb, kwargs)
    assert isinstance(storage, CosmosDBPipelineStorage)


def test_create_file_storage():
    kwargs = {"type": "file", "base_dir": "/tmp/teststorage"}
    storage = StorageFactory.create_storage(OutputType.file, kwargs)
    assert isinstance(storage, FilePipelineStorage)


def test_create_memory_storage():
    kwargs = {"type": "memory"}
    storage = StorageFactory.create_storage(OutputType.memory, kwargs)
    assert isinstance(storage, MemoryPipelineStorage)


def test_register_and_create_custom_storage():
    class CustomStorage:
        def __init__(self, **kwargs):
            pass

    StorageFactory.register("custom", CustomStorage)
    storage = StorageFactory.create_storage("custom", {})
    assert isinstance(storage, CustomStorage)


def test_create_unknown_storage():
    with pytest.raises(ValueError, match="Unknown storage type: unknown"):
        StorageFactory.create_storage("unknown", {})
