# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Factory functions for creating storage."""

from __future__ import annotations

from typing import cast

from graphrag.config.enums import StorageType
from graphrag.index.config.storage import (
    PipelineBlobStorageConfig,
    PipelineCosmosDBStorageConfig,
    PipelineFileStorageConfig,
    PipelineStorageConfig,
)
from graphrag.storage.blob_pipeline_storage import create_blob_storage
from graphrag.storage.cosmosdb_pipeline_storage import create_cosmosdb_storage
from graphrag.storage.file_pipeline_storage import create_file_storage
from graphrag.storage.memory_pipeline_storage import MemoryPipelineStorage


def create_storage(config: PipelineStorageConfig):
    """Create a storage object based on the config."""
    match config.type:
        case StorageType.memory:
            return MemoryPipelineStorage()
        case StorageType.blob:
            config = cast(PipelineBlobStorageConfig, config)
            return create_blob_storage(
                config.connection_string,
                config.storage_account_blob_url,
                config.container_name,
                config.base_dir,
            )
        case StorageType.cosmosdb:
            config = cast(PipelineCosmosDBStorageConfig, config)
            return create_cosmosdb_storage(
                connection_string=config.connection_string,
                cosmosdb_account_url=config.cosmosdb_account_url,
                container_name=config.container_name,
                base_dir=config.base_dir,
            )
        case StorageType.file:
            config = cast(PipelineFileStorageConfig, config)
            return create_file_storage(config.base_dir)
        case _:
            msg = f"Unknown storage type: {config.type}"
            raise ValueError(msg)
