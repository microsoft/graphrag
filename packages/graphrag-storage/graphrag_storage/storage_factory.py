# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License


"""Storage factory implementation."""

from collections.abc import Callable

from graphrag_common.factory import Factory

from graphrag_storage.storage import Storage
from graphrag_storage.storage_config import StorageConfig
from graphrag_storage.storage_type import StorageType


class _StorageFactory(Factory[Storage]):
    """A factory class for storage implementations."""


storage_factory = _StorageFactory()


def register_storage(
    storage_type: str, storage_initializer: Callable[..., Storage]
) -> None:
    """Register a custom storage implementation.

    Args
    ----
        - storage_type: str
            The storage id to register.
        - storage_initializer: Callable[..., Storage]
            The storage initializer to register.
    """
    storage_factory.register(storage_type, storage_initializer)


def create_storage(config: StorageConfig) -> Storage:
    """Create a storage implementation based on the given configuration.

    Args
    ----
        - config: StorageConfig
            The storage configuration to use.

    Returns
    -------
        Storage
            The created storage implementation.
    """
    config_model = config.model_dump()
    storage_strategy = config_model.pop("type")

    # Check storage_strategy is a string
    if not isinstance(storage_strategy, str):
        msg = f"StorageConfig.type must be a string, got {type(storage_strategy)}"
        raise TypeError(msg)

    if storage_strategy not in storage_factory:
        match storage_strategy:
            case StorageType.FILE:
                from graphrag_storage.file_storage import FileStorage

                register_storage(StorageType.FILE, FileStorage)
            case StorageType.MEMORY:
                from graphrag_storage.memory_storage import MemoryStorage

                register_storage(StorageType.MEMORY, MemoryStorage)
            case StorageType.AZURE_BLOB:
                from graphrag_storage.azure_blob_storage import AzureBlobStorage

                register_storage(StorageType.AZURE_BLOB, AzureBlobStorage)
            case StorageType.AZURE_COSMOS:
                from graphrag_storage.azure_cosmos_storage import AzureCosmosStorage

                register_storage(StorageType.AZURE_COSMOS, AzureCosmosStorage)
            case _:
                msg = f"StorageConfig.type '{storage_strategy}' is not registered in the StorageFactory. Registered types: {', '.join(storage_factory.keys())}."
                raise ValueError(msg)

    return storage_factory.create(storage_strategy, config_model)
