# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Default configuration methods definition."""

import json
import logging
from pathlib import Path

from graphrag.config.enums import (
    CacheType,
    InputFileType,
    ReportingType,
    StorageType,
    TextEmbeddingTarget,
)
from graphrag.config.models import (
    GraphRagConfig,
    TextEmbeddingConfig,
)
from graphrag.index.config.cache import (
    PipelineBlobCacheConfig,
    PipelineCacheConfigTypes,
    PipelineFileCacheConfig,
    PipelineMemoryCacheConfig,
    PipelineNoneCacheConfig,
)
from graphrag.index.config.embeddings import (
    all_embeddings,
    required_embeddings,
)
from graphrag.index.config.input import (
    PipelineCSVInputConfig,
    PipelineInputConfigTypes,
    PipelineTextInputConfig,
)
from graphrag.index.config.pipeline import (
    PipelineConfig,
)
from graphrag.index.config.reporting import (
    PipelineBlobReportingConfig,
    PipelineConsoleReportingConfig,
    PipelineFileReportingConfig,
    PipelineReportingConfigTypes,
)
from graphrag.index.config.storage import (
    PipelineBlobStorageConfig,
    PipelineFileStorageConfig,
    PipelineMemoryStorageConfig,
    PipelineStorageConfigTypes,
)
from graphrag.index.config.workflow import (
    PipelineWorkflowReference,
)
from graphrag.index.workflows.default_workflows import (
    create_base_entity_graph,
    create_base_text_units,
    create_final_communities,
    create_final_community_reports,
    create_final_covariates,
    create_final_documents,
    create_final_entities,
    create_final_nodes,
    create_final_relationships,
    create_final_text_units,
    generate_text_embeddings,
)

log = logging.getLogger(__name__)

builtin_document_attributes: set[str] = {
    "id",
    "source",
    "text",
    "title",
    "timestamp",
    "year",
    "month",
    "day",
    "hour",
    "minute",
    "second",
}


def create_pipeline_config(settings: GraphRagConfig, verbose=False) -> PipelineConfig:
    """Get the default config for the pipeline."""
    # relative to the root_dir
    if verbose:
        _log_llm_settings(settings)

    skip_workflows = settings.skip_workflows
    embedded_fields = _get_embedded_fields(settings)
    covariates_enabled = (
        settings.claim_extraction.enabled
        and create_final_covariates not in skip_workflows
    )

    result = PipelineConfig(
        root_dir=settings.root_dir,
        input=_get_pipeline_input_config(settings),
        reporting=_get_reporting_config(settings),
        storage=_get_storage_config(settings),
        cache=_get_cache_config(settings),
        workflows=[
            *_document_workflows(settings),
            *_text_unit_workflows(settings, covariates_enabled),
            *_graph_workflows(settings),
            *_community_workflows(settings, covariates_enabled),
            *(_covariate_workflows(settings) if covariates_enabled else []),
            *(_embeddings_workflows(settings, embedded_fields)),
        ],
    )

    # Remove any workflows that were specified to be skipped
    log.info("skipping workflows %s", ",".join(skip_workflows))
    result.workflows = [w for w in result.workflows if w.name not in skip_workflows]
    return result


def _get_embedded_fields(settings: GraphRagConfig) -> set[str]:
    match settings.embeddings.target:
        case TextEmbeddingTarget.all:
            return all_embeddings.difference(settings.embeddings.skip)
        case TextEmbeddingTarget.required:
            return required_embeddings
        case TextEmbeddingTarget.none:
            return set()
        case _:
            msg = f"Unknown embeddings target: {settings.embeddings.target}"
            raise ValueError(msg)


def _log_llm_settings(settings: GraphRagConfig) -> None:
    log.info(
        "Using LLM Config %s",
        json.dumps(
            {**settings.entity_extraction.llm.model_dump(), "api_key": "*****"},
            indent=4,
        ),
    )
    log.info(
        "Using Embeddings Config %s",
        json.dumps(
            {**settings.embeddings.llm.model_dump(), "api_key": "*****"}, indent=4
        ),
    )


def _document_workflows(
    settings: GraphRagConfig,
) -> list[PipelineWorkflowReference]:
    return [
        PipelineWorkflowReference(
            name=create_final_documents,
            config={
                "document_attribute_columns": list(
                    {*(settings.input.document_attribute_columns)}
                    - builtin_document_attributes
                ),
            },
        ),
    ]


def _text_unit_workflows(
    settings: GraphRagConfig,
    covariates_enabled: bool,
) -> list[PipelineWorkflowReference]:
    return [
        PipelineWorkflowReference(
            name=create_base_text_units,
            config={
                "chunk_by": settings.chunks.group_by_columns,
                "text_chunk": {
                    "strategy": settings.chunks.resolved_strategy(
                        settings.encoding_model
                    )
                },
            },
        ),
        PipelineWorkflowReference(
            name=create_final_text_units,
            config={
                "covariates_enabled": covariates_enabled,
            },
        ),
    ]


def _get_embedding_settings(
    settings: TextEmbeddingConfig,
    embedding_name: str,
    vector_store_params: dict | None = None,
) -> dict:
    vector_store_settings = settings.vector_store
    if vector_store_settings is None:
        return {"strategy": settings.resolved_strategy()}
    #
    # If we get to this point, settings.vector_store is defined, and there's a specific setting for this embedding.
    # settings.vector_store.base contains connection information, or may be undefined
    # settings.vector_store.<vector_name> contains the specific settings for this embedding
    #
    strategy = settings.resolved_strategy()  # get the default strategy
    strategy.update({
        "vector_store": {**(vector_store_params or {}), **vector_store_settings}
    })  # update the default strategy with the vector store settings
    # This ensures the vector store config is part of the strategy and not the global config
    return {
        "strategy": strategy,
        "embedding_name": embedding_name,
    }


def _graph_workflows(settings: GraphRagConfig) -> list[PipelineWorkflowReference]:
    return [
        PipelineWorkflowReference(
            name=create_base_entity_graph,
            config={
                "graphml_snapshot": settings.snapshots.graphml,
                "entity_extract": {
                    **settings.entity_extraction.parallelization.model_dump(),
                    "async_mode": settings.entity_extraction.async_mode,
                    "strategy": settings.entity_extraction.resolved_strategy(
                        settings.root_dir, settings.encoding_model
                    ),
                    "entity_types": settings.entity_extraction.entity_types,
                },
                "summarize_descriptions": {
                    **settings.summarize_descriptions.parallelization.model_dump(),
                    "async_mode": settings.summarize_descriptions.async_mode,
                    "strategy": settings.summarize_descriptions.resolved_strategy(
                        settings.root_dir,
                    ),
                },
                "embed_graph_enabled": settings.embed_graph.enabled,
                "cluster_graph": {
                    "strategy": settings.cluster_graph.resolved_strategy()
                },
                "embed_graph": {"strategy": settings.embed_graph.resolved_strategy()},
            },
        ),
        PipelineWorkflowReference(
            name=create_final_entities,
            config={},
        ),
        PipelineWorkflowReference(
            name=create_final_relationships,
            config={},
        ),
        PipelineWorkflowReference(
            name=create_final_nodes,
            config={
                "layout_graph_enabled": settings.umap.enabled,
                "snapshot_top_level_nodes": settings.snapshots.top_level_nodes,
            },
        ),
    ]


def _community_workflows(
    settings: GraphRagConfig, covariates_enabled: bool
) -> list[PipelineWorkflowReference]:
    return [
        PipelineWorkflowReference(name=create_final_communities),
        PipelineWorkflowReference(
            name=create_final_community_reports,
            config={
                "covariates_enabled": covariates_enabled,
                "create_community_reports": {
                    **settings.community_reports.parallelization.model_dump(),
                    "async_mode": settings.community_reports.async_mode,
                    "strategy": settings.community_reports.resolved_strategy(
                        settings.root_dir
                    ),
                },
            },
        ),
    ]


def _covariate_workflows(
    settings: GraphRagConfig,
) -> list[PipelineWorkflowReference]:
    return [
        PipelineWorkflowReference(
            name=create_final_covariates,
            config={
                "claim_extract": {
                    **settings.claim_extraction.parallelization.model_dump(),
                    "strategy": settings.claim_extraction.resolved_strategy(
                        settings.root_dir, settings.encoding_model
                    ),
                },
            },
        )
    ]


def _embeddings_workflows(
    settings: GraphRagConfig, embedded_fields: set[str]
) -> list[PipelineWorkflowReference]:
    return [
        PipelineWorkflowReference(
            name=generate_text_embeddings,
            config={
                "document_raw_content_embed": _get_embedding_settings(
                    settings.embeddings,
                    "document_raw_content",
                    {
                        "title_column": "raw_content",
                        "collection_name": "final_documents_raw_content_embedding",
                        "store_in_table": True,
                    },
                ),
                "text_unit_text_embed": _get_embedding_settings(
                    settings.embeddings,
                    "text_unit_text",
                    {
                        "title_column": "text",
                        "collection_name": "text_units_embedding",
                        "store_in_table": True,
                    },
                ),
                "entity_name_embed": _get_embedding_settings(
                    settings.embeddings,
                    "entity_name",
                    {
                        "title_column": "name",
                        "collection_name": "entity_name_embeddings",
                        "store_in_table": True,
                    },
                ),
                "entity_name_description_embed": _get_embedding_settings(
                    settings.embeddings,
                    "entity_name_description",
                    {
                        "title_column": "description",
                        "collection_name": "entity_description_embeddings",
                        "store_in_table": True,
                    },
                ),
                "relationship_description_embed": _get_embedding_settings(
                    settings.embeddings,
                    "relationship_description",
                    {
                        "title_column": "description",
                        "collection_name": "relationships_description_embeddings",
                        "store_in_table": True,
                    },
                ),
                "community_report_full_content_embed": _get_embedding_settings(
                    settings.embeddings,
                    "community_report_full_content",
                    {
                        "title_column": "full_content",
                        "collection_name": "final_community_reports_full_content_embedding",
                        "store_in_table": True,
                    },
                ),
                "community_report_summary_embed": _get_embedding_settings(
                    settings.embeddings,
                    "community_report_summary",
                    {
                        "title_column": "summary",
                        "collection_name": "final_community_reports_summary_embedding",
                        "store_in_table": True,
                    },
                ),
                "community_report_title_embed": _get_embedding_settings(
                    settings.embeddings,
                    "community_report_title",
                    {
                        "title_column": "title",
                        "store_in_table": True,
                        "collection_name": "final_community_reports_title_embedding",
                    },
                ),
                "embedded_fields": embedded_fields,
            },
        ),
    ]


def _get_pipeline_input_config(
    settings: GraphRagConfig,
) -> PipelineInputConfigTypes:
    file_type = settings.input.file_type
    match file_type:
        case InputFileType.csv:
            return PipelineCSVInputConfig(
                base_dir=settings.input.base_dir,
                file_pattern=settings.input.file_pattern,
                encoding=settings.input.encoding,
                source_column=settings.input.source_column,
                timestamp_column=settings.input.timestamp_column,
                timestamp_format=settings.input.timestamp_format,
                text_column=settings.input.text_column,
                title_column=settings.input.title_column,
                type=settings.input.type,
                connection_string=settings.input.connection_string,
                storage_account_blob_url=settings.input.storage_account_blob_url,
                container_name=settings.input.container_name,
            )
        case InputFileType.text:
            return PipelineTextInputConfig(
                base_dir=settings.input.base_dir,
                file_pattern=settings.input.file_pattern,
                encoding=settings.input.encoding,
                type=settings.input.type,
                connection_string=settings.input.connection_string,
                storage_account_blob_url=settings.input.storage_account_blob_url,
                container_name=settings.input.container_name,
            )
        case _:
            msg = f"Unknown input type: {file_type}"
            raise ValueError(msg)


def _get_reporting_config(
    settings: GraphRagConfig,
) -> PipelineReportingConfigTypes:
    """Get the reporting config from the settings."""
    match settings.reporting.type:
        case ReportingType.file:
            # relative to the root_dir
            return PipelineFileReportingConfig(base_dir=settings.reporting.base_dir)
        case ReportingType.blob:
            connection_string = settings.reporting.connection_string
            storage_account_blob_url = settings.reporting.storage_account_blob_url
            container_name = settings.reporting.container_name
            if container_name is None:
                msg = "Container name must be provided for blob reporting."
                raise ValueError(msg)
            if connection_string is None and storage_account_blob_url is None:
                msg = "Connection string or storage account blob url must be provided for blob reporting."
                raise ValueError(msg)
            return PipelineBlobReportingConfig(
                connection_string=connection_string,
                container_name=container_name,
                base_dir=settings.reporting.base_dir,
                storage_account_blob_url=storage_account_blob_url,
            )
        case ReportingType.console:
            return PipelineConsoleReportingConfig()
        case _:
            # relative to the root_dir
            return PipelineFileReportingConfig(base_dir=settings.reporting.base_dir)


def _get_storage_config(
    settings: GraphRagConfig,
) -> PipelineStorageConfigTypes:
    """Get the storage type from the settings."""
    root_dir = settings.root_dir
    match settings.storage.type:
        case StorageType.memory:
            return PipelineMemoryStorageConfig()
        case StorageType.file:
            # relative to the root_dir
            base_dir = settings.storage.base_dir
            if base_dir is None:
                msg = "Base directory must be provided for file storage."
                raise ValueError(msg)
            return PipelineFileStorageConfig(base_dir=str(Path(root_dir) / base_dir))
        case StorageType.blob:
            connection_string = settings.storage.connection_string
            storage_account_blob_url = settings.storage.storage_account_blob_url
            container_name = settings.storage.container_name
            if container_name is None:
                msg = "Container name must be provided for blob storage."
                raise ValueError(msg)
            if connection_string is None and storage_account_blob_url is None:
                msg = "Connection string or storage account blob url must be provided for blob storage."
                raise ValueError(msg)
            return PipelineBlobStorageConfig(
                connection_string=connection_string,
                container_name=container_name,
                base_dir=settings.storage.base_dir,
                storage_account_blob_url=storage_account_blob_url,
            )
        case _:
            # relative to the root_dir
            base_dir = settings.storage.base_dir
            if base_dir is None:
                msg = "Base directory must be provided for file storage."
                raise ValueError(msg)
            return PipelineFileStorageConfig(base_dir=str(Path(root_dir) / base_dir))


def _get_cache_config(
    settings: GraphRagConfig,
) -> PipelineCacheConfigTypes:
    """Get the cache type from the settings."""
    match settings.cache.type:
        case CacheType.memory:
            return PipelineMemoryCacheConfig()
        case CacheType.file:
            # relative to root dir
            return PipelineFileCacheConfig(base_dir=settings.cache.base_dir)
        case CacheType.none:
            return PipelineNoneCacheConfig()
        case CacheType.blob:
            connection_string = settings.cache.connection_string
            storage_account_blob_url = settings.cache.storage_account_blob_url
            container_name = settings.cache.container_name
            if container_name is None:
                msg = "Container name must be provided for blob cache."
                raise ValueError(msg)
            if connection_string is None and storage_account_blob_url is None:
                msg = "Connection string or storage account blob url must be provided for blob cache."
                raise ValueError(msg)
            return PipelineBlobCacheConfig(
                connection_string=connection_string,
                container_name=container_name,
                base_dir=settings.cache.base_dir,
                storage_account_blob_url=storage_account_blob_url,
            )
        case _:
            # relative to root dir
            return PipelineFileCacheConfig(base_dir="./cache")
