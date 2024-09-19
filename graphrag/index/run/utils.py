# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Utility functions for the GraphRAG run module."""

import logging
from string import Template
from typing import Any

import pandas as pd
from datashaper import (
    WorkflowCallbacks,
)

from graphrag.index.cache.memory_pipeline_cache import InMemoryCache
from graphrag.index.cache.pipeline_cache import PipelineCache
from graphrag.index.config.cache import (
    PipelineBlobCacheConfig,
    PipelineFileCacheConfig,
)
from graphrag.index.config.input import PipelineInputConfigTypes
from graphrag.index.config.pipeline import PipelineConfig
from graphrag.index.config.reporting import (
    PipelineBlobReportingConfig,
    PipelineFileReportingConfig,
    PipelineReportingConfigTypes,
)
from graphrag.index.config.storage import (
    PipelineBlobStorageConfig,
    PipelineFileStorageConfig,
)
from graphrag.index.context import PipelineRunContext, PipelineRunStats
from graphrag.index.input import load_input
from graphrag.index.progress.types import ProgressReporter
from graphrag.index.reporting import load_pipeline_reporter
from graphrag.index.storage.memory_pipeline_storage import MemoryPipelineStorage
from graphrag.index.storage.typing import PipelineStorage

log = logging.getLogger(__name__)


def _create_reporter(
    config: PipelineReportingConfigTypes | None, root_dir: str
) -> WorkflowCallbacks | None:
    """Create the reporter for the pipeline."""
    return load_pipeline_reporter(config, root_dir) if config else None


async def _create_input(
    config: PipelineInputConfigTypes | None,
    progress_reporter: ProgressReporter | None,
    root_dir: str,
) -> pd.DataFrame | None:
    """Load the input for the pipeline."""
    if config is None:
        return None

    return await load_input(config, progress_reporter, root_dir)


def _validate_dataset(dataset: Any):
    """Validate the dataset for the pipeline.

    Args:
        - dataset - The dataset to validate
    """
    if not isinstance(dataset, pd.DataFrame):
        msg = "Dataset must be a pandas dataframe!"
        raise TypeError(msg)


def _apply_substitutions(config: PipelineConfig, run_id: str) -> PipelineConfig:
    """Apply the substitutions to the configuration."""
    substitutions = {"timestamp": run_id}

    if (
        isinstance(
            config.storage, PipelineFileStorageConfig | PipelineBlobStorageConfig
        )
        and config.storage.base_dir
    ):
        config.storage.base_dir = Template(config.storage.base_dir).substitute(
            substitutions
        )
    if (
        isinstance(config.cache, PipelineFileCacheConfig | PipelineBlobCacheConfig)
        and config.cache.base_dir
    ):
        config.cache.base_dir = Template(config.cache.base_dir).substitute(
            substitutions
        )

    if (
        isinstance(
            config.reporting, PipelineFileReportingConfig | PipelineBlobReportingConfig
        )
        and config.reporting.base_dir
    ):
        config.reporting.base_dir = Template(config.reporting.base_dir).substitute(
            substitutions
        )

    return config


def _create_run_context(
    storage: PipelineStorage | None,
    cache: PipelineCache | None,
    stats: PipelineRunStats | None,
) -> PipelineRunContext:
    """Create the run context for the pipeline."""
    return PipelineRunContext(
        stats=stats or PipelineRunStats(),
        cache=cache or InMemoryCache(),
        storage=storage or MemoryPipelineStorage(),
    )
