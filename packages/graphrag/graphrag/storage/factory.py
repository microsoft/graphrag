# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Factory functions for creating storage."""

from __future__ import annotations

from graphrag_factory import Factory

from graphrag.config.enums import StorageType
from graphrag.storage.blob_pipeline_storage import BlobPipelineStorage
from graphrag.storage.cosmosdb_pipeline_storage import CosmosDBPipelineStorage
from graphrag.storage.file_pipeline_storage import FilePipelineStorage
from graphrag.storage.memory_pipeline_storage import MemoryPipelineStorage
from graphrag.storage.pipeline_storage import PipelineStorage


class StorageFactory(Factory[PipelineStorage]):
    """A factory class for storage implementations.

    Includes a method for users to register a custom storage implementation.

    Configuration arguments are passed to each storage implementation as kwargs
    for individual enforcement of required/optional arguments.
    """


# --- register built-in storage implementations ---
storage_factory = StorageFactory()
storage_factory.register(StorageType.blob.value, BlobPipelineStorage)
storage_factory.register(StorageType.cosmosdb.value, CosmosDBPipelineStorage)
storage_factory.register(StorageType.file.value, FilePipelineStorage)
storage_factory.register(StorageType.memory.value, MemoryPipelineStorage)
