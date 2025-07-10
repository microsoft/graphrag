# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Factory functions for creating storage."""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, ClassVar

from graphrag.config.enums import StorageType
from graphrag.storage.blob_pipeline_storage import create_blob_storage
from graphrag.storage.cosmosdb_pipeline_storage import create_cosmosdb_storage
from graphrag.storage.file_pipeline_storage import create_file_storage
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

    _storage_registry: ClassVar[dict[str, Callable[..., PipelineStorage]]] = {}
    storage_types: ClassVar[dict[str, type]] = {}  # For backward compatibility

    @classmethod
    def register(
        cls, storage_type: str, creator: Callable[..., PipelineStorage]
    ) -> None:
        """Register a custom storage implementation.

        Args:
            storage_type: The type identifier for the storage.
            creator: A callable that creates an instance of the storage.
        """
        cls._storage_registry[storage_type] = creator

        # For backward compatibility with code that may access storage_types directly
        if (
            callable(creator)
            and hasattr(creator, "__annotations__")
            and "return" in creator.__annotations__
        ):
            with suppress(TypeError, KeyError):
                cls.storage_types[storage_type] = creator.__annotations__["return"]

    @classmethod
    def create_storage(
        cls, storage_type: StorageType | str, kwargs: dict
    ) -> PipelineStorage:
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
        storage_type_str = (
            storage_type.value
            if isinstance(storage_type, StorageType)
            else storage_type
        )

        if storage_type_str not in cls._storage_registry:
            msg = f"Unknown storage type: {storage_type}"
            raise ValueError(msg)

        return cls._storage_registry[storage_type_str](**kwargs)

    @classmethod
    def get_storage_types(cls) -> list[str]:
        """Get the registered storage implementations."""
        return list(cls._storage_registry.keys())

    @classmethod
    def is_supported_storage_type(cls, storage_type: str) -> bool:
        """Check if the given storage type is supported."""
        return storage_type in cls._storage_registry


# --- Register default implementations ---
StorageFactory.register(StorageType.blob.value, create_blob_storage)
StorageFactory.register(StorageType.cosmosdb.value, create_cosmosdb_storage)
StorageFactory.register(StorageType.file.value, create_file_storage)
StorageFactory.register(StorageType.memory.value, lambda **_: MemoryPipelineStorage())
