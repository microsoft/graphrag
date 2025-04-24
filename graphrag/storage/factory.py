# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Factory functions for creating storage."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from graphrag.config.enums import OutputType
from graphrag.storage.blob_pipeline_storage import create_blob_storage
from graphrag.storage.cosmosdb_pipeline_storage import create_cosmosdb_storage
from graphrag.storage.file_pipeline_storage import create_file_storage
from graphrag.storage.memory_pipeline_storage import MemoryPipelineStorage

if TYPE_CHECKING:
    from graphrag.storage.pipeline_storage import PipelineStorage


class StorageFactory:
    """A factory class for storage implementations.

    Includes a method for users to register a custom storage implementation.

    Configuration arguments are passed to each storage implementation as kwargs
    for individual enforcement of required/optional arguments.
    """

    storage_types: ClassVar[dict[str, type]] = {}

    @classmethod
    def register(cls, storage_type: str, storage: type):
        """Register a custom storage implementation."""
        cls.storage_types[storage_type] = storage

    @classmethod
    def create_storage(
        cls, storage_type: OutputType | str, kwargs: dict
    ) -> PipelineStorage:
        """Get a storage object from the provided type."""
        if storage_type not in cls.storage_types:
            msg = f"Storage implementation '{storage_type}' is not registered."
            raise ValueError(msg)
        return cls.storage_types[storage_type](**kwargs)


StorageFactory.register(OutputType.blob, OutputType.blob, create_blob_storage)
StorageFactory.register(
    OutputType.cosmosdb, OutputType.cosmosdb, create_cosmosdb_storage
)
StorageFactory.register(OutputType.file, OutputType.file, create_file_storage)
StorageFactory.register(OutputType.memory, OutputType.memory, MemoryPipelineStorage)
