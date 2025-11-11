# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License


"""Storage factory implementation."""

from collections.abc import Callable

from graphrag_common.factory import Factory

from graphrag_storage.azure_blob_storage import AzureBlobStorage
from graphrag_storage.azure_cosmos_storage import AzureCosmosStorage
from graphrag_storage.file_storage import FileStorage
from graphrag_storage.memory_storage import MemoryStorage
from graphrag_storage.storage import Storage
from graphrag_storage.storage_config import StorageConfig


class _StorageFactory(Factory[Storage]):
    """A factory class for storage implementations.

    Includes a method for users to register a custom storage implementation.

    Configuration arguments are passed to each storage implementation as kwargs
    for individual enforcement of required/optional arguments.
    """


storage_factory = _StorageFactory()
storage_factory.register(FileStorage.__name__, FileStorage)
storage_factory.register(MemoryStorage.__name__, MemoryStorage)
storage_factory.register(AzureBlobStorage.__name__, AzureBlobStorage)
storage_factory.register(AzureCosmosStorage.__name__, AzureCosmosStorage)


def register_storage(storage: str, storage_initializer: Callable[..., Storage]) -> None:
    """Register a custom storage implementation.

    Args
    ----
        - storage: str
            The storage id to register.
        - storage_initializer: Callable[..., Storage]
            The storage initializer to register.
    """
    storage_factory.register(storage, storage_initializer)


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
    storage_strategy = config.type

    if storage_strategy not in storage_factory:
        msg = f"StorageConfig.type '{storage_strategy}' is not registered in the StorageFactory. Registered types: {', '.join(storage_factory.keys())}."
        raise ValueError(msg)

    return storage_factory.create(config.type, config.model_dump())
