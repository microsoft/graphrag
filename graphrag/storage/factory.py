# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Factory functions for creating storage."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from graphrag.config.enums import StorageType
from graphrag.storage.blob_pipeline_storage import BlobPipelineStorage
from graphrag.storage.cosmosdb_pipeline_storage import CosmosDBPipelineStorage
from graphrag.storage.file_pipeline_storage import FilePipelineStorage
from graphrag.storage.memory_pipeline_storage import MemoryPipelineStorage

if TYPE_CHECKING:
    from collections.abc import Callable

    from graphrag.storage.pipeline_storage import PipelineStorage


class StorageFactory:
    """A factory class for storage implementations.

    Includes a method for users to register a custom storage implementation.

    Configuration arguments are passed to each storage implementation as kwargs
    for individual enforcement of required/optional arguments.
    """

    _registry: ClassVar[dict[str, Callable[..., PipelineStorage]]] = {}

    @classmethod
    def register(
        cls, storage_type: str, creator: Callable[..., PipelineStorage]
    ) -> None:
        """Register a custom storage implementation.

        Args:
            storage_type: The type identifier for the storage.
            creator: A class or callable that creates an instance of PipelineStorage.

        """
        cls._registry[storage_type] = creator

    @classmethod
    def create_storage(cls, storage_type: str, kwargs: dict) -> PipelineStorage:
        """Create a storage object from the provided type.

        Args:
            storage_type: The type of storage to create.
            kwargs: Additional keyword arguments for the storage constructor.

        Returns
        -------
            A PipelineStorage instance.

        Raises
        ------
            ValueError: If the storage type is not registered.
        """
        if storage_type not in cls._registry:
            msg = f"Unknown storage type: {storage_type}"
            raise ValueError(msg)

        return cls._registry[storage_type](**kwargs)

    @classmethod
    def get_storage_types(cls) -> list[str]:
        """Get the registered storage implementations."""
        return list(cls._registry.keys())

    @classmethod
    def is_supported_type(cls, storage_type: str) -> bool:
        """Check if the given storage type is supported."""
        return storage_type in cls._registry


# --- register built-in storage implementations ---
StorageFactory.register(StorageType.blob.value, BlobPipelineStorage)
StorageFactory.register(StorageType.cosmosdb.value, CosmosDBPipelineStorage)
StorageFactory.register(StorageType.file.value, FilePipelineStorage)
StorageFactory.register(StorageType.memory.value, MemoryPipelineStorage)
