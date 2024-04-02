# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""The Indexing Engine package root."""

import argparse

from .cache import PipelineCache
from .cli import index_cli
from .config import (
    PipelineBlobCacheConfig,
    PipelineBlobReportingConfig,
    PipelineBlobStorageConfig,
    PipelineCacheConfig,
    PipelineCacheConfigTypes,
    PipelineCacheType,
    PipelineConfig,
    PipelineConsoleReportingConfig,
    PipelineCSVInputConfig,
    PipelineFileCacheConfig,
    PipelineFileReportingConfig,
    PipelineFileStorageConfig,
    PipelineInputConfig,
    PipelineInputConfigTypes,
    PipelineInputType,
    PipelineMemoryCacheConfig,
    PipelineMemoryStorageConfig,
    PipelineNoneCacheConfig,
    PipelineReportingConfig,
    PipelineReportingConfigTypes,
    PipelineReportingType,
    PipelineStorageConfig,
    PipelineStorageConfigTypes,
    PipelineStorageType,
    PipelineTextInputConfig,
    PipelineWorkflowConfig,
    PipelineWorkflowReference,
    PipelineWorkflowStep,
)
from .default_config import (
    CacheConfigModel,
    ChunkingConfigModel,
    ClaimExtractionConfigModel,
    ClusterGraphConfigModel,
    CommunityReportsConfigModel,
    DefaultConfigParametersModel,
    EmbedGraphConfigModel,
    EntityExtractionConfigModel,
    InputConfigModel,
    LLMConfigModel,
    LLMParametersModel,
    ParallelizationParametersModel,
    ReportingConfigModel,
    SnapshotsConfigModel,
    StorageConfigModel,
    SummarizeDescriptionsConfigModel,
    TextEmbeddingConfigModel,
    UmapConfigModel,
    default_config,
    default_config_parameters,
    default_config_parameters_from_env_vars,
)
from .run import run_pipeline, run_pipeline_with_config
from .storage import PipelineStorage

__all__ = [
    "CacheConfigModel",
    "ChunkingConfigModel",
    "ClaimExtractionConfigModel",
    "ClusterGraphConfigModel",
    "CommunityReportsConfigModel",
    "DefaultConfigParametersModel",
    "EmbedGraphConfigModel",
    "EntityExtractionConfigModel",
    "InputConfigModel",
    "LLMConfigModel",
    "LLMParametersModel",
    "ParallelizationParametersModel",
    "PipelineBlobCacheConfig",
    "PipelineBlobCacheConfig",
    "PipelineBlobReportingConfig",
    "PipelineBlobStorageConfig",
    "PipelineCSVInputConfig",
    "PipelineCache",
    "PipelineCacheConfig",
    "PipelineCacheConfigTypes",
    # Deep Config Stack
    "PipelineCacheType",
    "PipelineConfig",
    "PipelineConsoleReportingConfig",
    "PipelineFileCacheConfig",
    "PipelineFileReportingConfig",
    "PipelineFileStorageConfig",
    "PipelineInputConfig",
    "PipelineInputConfigTypes",
    "PipelineInputType",
    "PipelineMemoryCacheConfig",
    "PipelineMemoryStorageConfig",
    "PipelineNoneCacheConfig",
    "PipelineReportingConfig",
    "PipelineReportingConfigTypes",
    "PipelineReportingType",
    "PipelineStorage",
    "PipelineStorageConfig",
    "PipelineStorageConfigTypes",
    "PipelineStorageType",
    "PipelineTextInputConfig",
    "PipelineWorkflowConfig",
    "PipelineWorkflowReference",
    "PipelineWorkflowStep",
    "ReportingConfigModel",
    "SnapshotsConfigModel",
    "StorageConfigModel",
    "SummarizeDescriptionsConfigModel",
    "TextEmbeddingConfigModel",
    "UmapConfigModel",
    # Default Config Stack
    "default_config",
    "default_config_parameters",
    "default_config_parameters_from_env_vars",
    "run_pipeline",
    "run_pipeline_with_config",
]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        help="The configuration yaml file to use when running the pipeline",
        required=False,
        type=str,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Runs the pipeline with verbose logging",
        action="store_true",
    )
    parser.add_argument(
        "--memprofile",
        help="Runs the pipeline with memory profiling",
        action="store_true",
    )
    parser.add_argument(
        "--root",
        help="If no configuration is defined, the root directory to use for input data and output data",
        # Only required if config is not defined
        required=False,
        type=str,
    )
    parser.add_argument(
        "--resume",
        help="Resume a given data run leveraging Parquet output files.",
        # Only required if config is not defined
        required=False,
        type=str,
    )
    parser.add_argument(
        "--reporter",
        help="The progress reporter to use. Valid values are 'rich', 'print', or 'none'",
        type=str,
    )
    parser.add_argument(
        "--emit",
        help="The data formats to emit, comma-separated. Valid values are 'parquet' and 'csv'. default='parquet,csv'",
        type=str,
    )
    parser.add_argument("--nocache", help="Disable LLM cache.", action="store_true")
    args = parser.parse_args()

    index_cli(
        root=args.root,
        verbose=args.verbose,
        resume=args.resume,
        memprofile=args.memprofile,
        nocache=args.nocache,
        reporter=args.reporter,
        config=args.config,
        emit=args.emit,
        cli=True,
    )
