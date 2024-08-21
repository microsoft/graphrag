# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing load_storage method definition."""

from __future__ import annotations

from typing import cast

from graphrag.config import StorageType
from graphrag.index.config.storage import (
    PipelineBlobStorageConfig,
    PipelineFileStorageConfig,
    PipelineMinioStorageConfig,
    PipelineStorageConfig,
)

from .blob_pipeline_storage import create_blob_storage
from .file_pipeline_storage import create_file_storage
from .memory_pipeline_storage import create_memory_storage
from .minio_pipeline_storage import create_minio_storage


def load_storage(config: PipelineStorageConfig):
    """Load the storage for a pipeline."""
    match config.type:
        case StorageType.memory:
            return create_memory_storage()
        case StorageType.blob:
            config = cast(PipelineBlobStorageConfig, config)
            return create_blob_storage(
                config.connection_string,
                config.storage_account_blob_url,
                config.container_name,
                config.base_dir,
            )
        case StorageType.file:
            config = cast(PipelineFileStorageConfig, config)
            return create_file_storage(config.base_dir)
        case StorageType.minio:
            config = cast(PipelineMinioStorageConfig, config)
            return create_minio_storage( endpoint=config.endpoint if config.endpoint else ""
                                        ,base_dir= config.base_dir if config.base_dir else ""
                                        ,bucket_name= config.bucket_name if config.bucket_name else ""
                                        ,access_key= config.access_key if config.access_key else ""
                                        ,secret_key= config.secret_key if config.secret_key else ""
                                        )
        case _:
            msg = f"Unknown storage type: {config.type}"
            raise ValueError(msg)
