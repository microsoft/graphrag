# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Factory functions for creating storage."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from graphrag.config.enums import StorageType
from graphrag.storage.blob_pipeline_storage import create_blob_storage
from graphrag.storage.cosmosdb_pipeline_storage import create_cosmosdb_storage
from graphrag.storage.file_pipeline_storage import create_file_storage
from graphrag.storage.memory_pipeline_storage import MemoryPipelineStorage

if TYPE_CHECKING:
    from graphrag.storage.pipeline_storage import PipelineStorage


class StorageFactory:
    """A factory class for storage implementations.

    Includes a method for users to register a custom storage implementation.
    """

    storage_types: ClassVar[dict[str, type]] = {}

    @classmethod
    def register(cls, storage_type: str, storage: type):
        """Register a custom storage implementation."""
        cls.storage_types[storage_type] = storage

    @classmethod
    def create_storage(
        cls, storage_type: StorageType | str, kwargs: dict
    ) -> PipelineStorage:
        """Create or get a storage object from the provided type."""
        match storage_type:
            case StorageType.blob:
                return create_blob_storage(**kwargs)
            case StorageType.cosmosdb:
                return create_cosmosdb_storage(**kwargs)
            case StorageType.file:
                return create_file_storage(**kwargs)
            case StorageType.memory:
                return MemoryPipelineStorage()
            case _:
                if storage_type in cls.storage_types:
                    return cls.storage_types[storage_type](**kwargs)
                msg = f"Unknown storage type: {storage_type}"
                raise ValueError(msg)
