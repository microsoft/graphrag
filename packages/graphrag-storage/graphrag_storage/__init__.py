# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The GraphRAG Storage package."""

from graphrag_storage.storage import Storage
from graphrag_storage.storage_config import StorageConfig
from graphrag_storage.storage_factory import (
    create_storage,
    register_storage,
)
from graphrag_storage.storage_type import StorageType
from graphrag_storage.tables import TableProvider

__all__ = [
    "Storage",
    "StorageConfig",
    "StorageType",
    "TableProvider",
    "create_storage",
    "register_storage",
]
