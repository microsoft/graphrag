# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The GraphRAG Storage package."""

from graphrag_storage.storage import Storage
from graphrag_storage.storage_config import StorageConfig
from graphrag_storage.storage_factory import create_storage, register_storage

__all__ = [
    "Storage",
    "StorageConfig",
    "create_storage",
    "register_storage",
]
