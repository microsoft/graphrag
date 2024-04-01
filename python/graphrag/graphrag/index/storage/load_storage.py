#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""A module containing load_storage method definition."""
from __future__ import annotations

from typing import cast

from graphrag.index.config import (
    PipelineBlobStorageConfig,
    PipelineFileStorageConfig,
    PipelineStorageConfig,
    PipelineStorageType,
)

from .blob_pipeline_storage import create_blob_storage
from .file_pipeline_storage import create_file_storage
from .memory_pipeline_storage import create_memory_storage


def load_storage(config: PipelineStorageConfig):
    """Load the storage for a pipeline."""
    match config.type:
        case PipelineStorageType.memory:
            return create_memory_storage()
        case PipelineStorageType.blob:
            config = cast(PipelineBlobStorageConfig, config)
            return create_blob_storage(
                config.connection_string, config.container_name, config.base_dir
            )
        case PipelineStorageType.file:
            config = cast(PipelineFileStorageConfig, config)
            return create_file_storage(config.base_dir)
        case _:
            msg = f"Unknown storage type: {config.type}"
            raise ValueError(msg)
