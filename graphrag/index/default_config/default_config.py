# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Default configuration methods definition."""

import json
import logging
from pathlib import Path

from graphrag.index.config import (
    PipelineBlobCacheConfig,
    PipelineBlobReportingConfig,
    PipelineBlobStorageConfig,
    PipelineCacheConfigTypes,
    PipelineCacheType,
    PipelineConfig,
    PipelineConsoleReportingConfig,
    PipelineCSVInputConfig,
    PipelineFileCacheConfig,
    PipelineFileReportingConfig,
    PipelineFileStorageConfig,
    PipelineInputConfigTypes,
    PipelineInputType,
    PipelineMemoryCacheConfig,
    PipelineMemoryStorageConfig,
    PipelineNoneCacheConfig,
    PipelineReportingConfigTypes,
    PipelineReportingType,
    PipelineStorageConfigTypes,
    PipelineStorageType,
    PipelineTextInputConfig,
    PipelineWorkflowReference,
)
from graphrag.index.default_config.parameters.models import TextEmbeddingTarget
from graphrag.index.workflows.default_workflows import (
    create_base_documents,
    create_base_entity_graph,
    create_base_extracted_entities,
    create_base_text_units,
    create_final_communities,
    create_final_community_reports,
    create_final_covariates,
    create_final_documents,
    create_final_entities,
    create_final_nodes,
    create_final_relationships,
    create_final_text_units,
    create_summarized_entities,
    join_text_units_to_covariate_ids,
    join_text_units_to_entity_ids,
    join_text_units_to_relationship_ids,
)

from .constants import (
    all_embeddings,
    builtin_document_attributes,
    community_full_content_embedding,
    community_summary_embedding,
    community_title_embedding,
    document_raw_content_embedding,
    entity_description_embedding,
    entity_name_embedding,
    relationship_description_embedding,
    required_embeddings,
)
from .parameters.default_config_parameters import DefaultConfigParametersDict

log = logging.getLogger(__name__)


def default_config(
    settings: DefaultConfigParametersDict, verbose=False
) -> PipelineConfig:
    """Get the default config for the pipeline."""
    root_dir = settings.root_dir

    # relative to the root_dir
    if verbose:
        _log_llm_settings(settings)

    skip_workflows = _determine_skip_workflows(settings)
    embedded_fields = _get_embedded_fields(settings)

    result = PipelineConfig(
        root_dir=root_dir,
        input=_get_pipeline_input_config(settings),
        reporting=_get_reporting_config(settings),
        storage=_get_storage_config(settings),
        cache=_get_cache_config(settings),
        workflows=[
            *_document_workflows(settings, embedded_fields),
            *_text_unit_workflows(settings, skip_workflows),
            *_graph_workflows(settings, embedded_fields),
            *_community_workflows(settings, embedded_fields),
            *_covariate_workflows(settings),
        ],
    )

    # Remove any workflows that were specified to be skipped
    log.info("skipping workflows %s", ",".join(skip_workflows))
    result.workflows = [w for w in result.workflows if w.name not in skip_workflows]
    return result


def _get_embedded_fields(settings: DefaultConfigParametersDict) -> list[str]:
    match settings.embeddings.target:
        case TextEmbeddingTarget.all:
            return list(all_embeddings - {*settings.embeddings.skip})
        case TextEmbeddingTarget.required:
            return list(required_embeddings)
        case _:
            msg = f"Unknown embeddings target: {settings.embeddings.target}"
            raise ValueError(msg)


def _determine_skip_workflows(settings: DefaultConfigParametersDict) -> list[str]:
    skip_workflows = settings.skip_workflows
    if (
        create_final_covariates in skip_workflows
        and join_text_units_to_covariate_ids not in skip_workflows
    ):
        skip_workflows.append(join_text_units_to_covariate_ids)
    return skip_workflows


def _log_llm_settings(settings: DefaultConfigParametersDict) -> None:
    log.info(
        "Using LLM Config",
        json.dumps({**settings.entity_extraction.llm, "api_key": "*****"}, indent=4),
    )
    log.info(
        "Using Embeddings Config",
        json.dumps({**settings.embeddings.llm, "api_key": "*****"}, indent=4),
    )


def _document_workflows(
    settings: DefaultConfigParametersDict, embedded_fields: list[str]
) -> list[PipelineWorkflowReference]:
    skip_document_raw_content_embedding = (
        document_raw_content_embedding not in embedded_fields
    )
    return [
        PipelineWorkflowReference(
            name=create_base_documents,
            config={
                "document_attribute_columns": list(
                    {*settings.input.document_attribute_columns}
                    - builtin_document_attributes
                )
            },
        ),
        PipelineWorkflowReference(
            name=create_final_documents,
            config={
                "text_embed": {"strategy": settings.embeddings.strategy},
                "skip_raw_content_embedding": skip_document_raw_content_embedding,
            },
        ),
    ]


def _text_unit_workflows(
    settings: DefaultConfigParametersDict, skip_workflows: list[str]
) -> list[PipelineWorkflowReference]:
    return [
        PipelineWorkflowReference(
            name=create_base_text_units,
            config={
                "chunk_by": settings.chunks.group_by_columns,
                "text_chunk": {"strategy": settings.chunks.strategy},
            },
        ),
        PipelineWorkflowReference(
            name=join_text_units_to_entity_ids,
        ),
        PipelineWorkflowReference(
            name=join_text_units_to_relationship_ids,
        ),
        PipelineWorkflowReference(
            name=join_text_units_to_covariate_ids,
        ),
        PipelineWorkflowReference(
            name=create_final_text_units,
            config={
                "text_embed": {"strategy": settings.embeddings.strategy},
                "covariates_enabled": create_final_covariates not in skip_workflows,
            },
        ),
    ]


def _graph_workflows(
    settings: DefaultConfigParametersDict, embedded_fields: list[str]
) -> list[PipelineWorkflowReference]:
    skip_entity_name_embedding = entity_name_embedding not in embedded_fields
    skip_entity_description_embedding = (
        entity_description_embedding not in embedded_fields
    )
    skip_relationship_description_embedding = (
        relationship_description_embedding not in embedded_fields
    )
    return [
        PipelineWorkflowReference(
            name=create_base_extracted_entities,
            config={
                "graphml_snapshot": settings.snapshots.graphml,
                "raw_entity_snapshot": settings.snapshots.raw_entities,
                "entity_extract": {
                    **settings.entity_extraction.parallelization,
                    "async_mode": settings.entity_extraction.async_mode,
                    "strategy": settings.entity_extraction.strategy,
                    "entity_types": settings.entity_extraction.entity_types,
                },
            },
        ),
        PipelineWorkflowReference(
            name=create_summarized_entities,
            config={
                "graphml_snapshot": settings.snapshots.graphml,
                "summarize_descriptions": {
                    **settings.summarize_descriptions.parallelization,
                    "async_mode": settings.summarize_descriptions.async_mode,
                    "strategy": settings.summarize_descriptions.strategy,
                },
            },
        ),
        PipelineWorkflowReference(
            name=create_base_entity_graph,
            config={
                "graphml_snapshot": settings.snapshots.graphml,
                "embed_graph_enabled": settings.embed_graph.is_enabled,
                "cluster_graph": {"strategy": settings.cluster_graph.strategy},
                "embed_graph": {"strategy": settings.embed_graph.strategy},
            },
        ),
        PipelineWorkflowReference(
            name=create_final_entities,
            config={
                "text_embed": {"strategy": settings.embeddings.strategy},
                "skip_name_embedding": skip_entity_name_embedding,
                "skip_description_embedding": skip_entity_description_embedding,
            },
        ),
        PipelineWorkflowReference(
            name=create_final_relationships,
            config={
                "text_embed": {"strategy": settings.embeddings.strategy},
                "skip_description_embedding": skip_relationship_description_embedding,
            },
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
    settings: DefaultConfigParametersDict, embedded_fields: list[str]
) -> list[PipelineWorkflowReference]:
    skip_community_title_embedding = community_title_embedding not in embedded_fields
    skip_community_summary_embedding = (
        community_summary_embedding not in embedded_fields
    )
    skip_community_full_content_embedding = (
        community_full_content_embedding not in embedded_fields
    )
    return [
        PipelineWorkflowReference(name=create_final_communities),
        PipelineWorkflowReference(
            name=create_final_community_reports,
            config={
                "skip_title_embedding": skip_community_title_embedding,
                "skip_summary_embedding": skip_community_summary_embedding,
                "skip_full_content_embedding": skip_community_full_content_embedding,
                "create_community_reports": {
                    **settings.community_reports.parallelization,
                    "async_mode": settings.community_reports.async_mode,
                    "strategy": settings.community_reports.strategy,
                },
                "text_embed": {"strategy": settings.embeddings.strategy},
            },
        ),
    ]


def _covariate_workflows(
    settings: DefaultConfigParametersDict,
) -> list[PipelineWorkflowReference]:
    return [
        PipelineWorkflowReference(
            name=create_final_covariates,
            config={
                "claim_extract": {
                    **settings.claim_extraction.parallelization,
                    "strategy": settings.claim_extraction.strategy,
                },
            },
        )
    ]


def _get_pipeline_input_config(
    settings: DefaultConfigParametersDict,
) -> PipelineInputConfigTypes:
    input_type = settings.input.type
    match input_type:
        case PipelineInputType.csv:
            return PipelineCSVInputConfig(
                base_dir=settings.input.base_dir,
                file_pattern=settings.input.file_pattern,
                encoding=settings.input.file_encoding,
                source_column=settings.input.source_column,
                timestamp_column=settings.input.timestamp_column,
                timestamp_format=settings.input.timestamp_format,
                text_column=settings.input.text_column,
                title_column=settings.input.title_column,
                storage_type=settings.input.storage_type,
                connection_string=settings.input.connection_string,
                container_name=settings.input.container_name,
            )
        case PipelineInputType.text:
            return PipelineTextInputConfig(
                base_dir=settings.input.base_dir,
                file_pattern=settings.input.file_pattern,
                encoding=settings.input.file_encoding,
                storage_type=settings.input.storage_type,
                connection_string=settings.input.connection_string,
                container_name=settings.input.container_name,
            )
        case _:
            msg = f"Unknown input type: {input_type}"
            raise ValueError(msg)


def _get_reporting_config(
    settings: DefaultConfigParametersDict,
) -> PipelineReportingConfigTypes:
    """Get the reporting config from the settings."""
    match settings.reporting.type:
        case PipelineReportingType.file:
            # relative to the root_dir
            return PipelineFileReportingConfig(base_dir=settings.reporting.base_dir)
        case PipelineReportingType.blob:
            return PipelineBlobReportingConfig(
                connection_string=settings.reporting.connection_string,
                container_name=settings.reporting.container_name,
                base_dir=settings.reporting.base_dir,
            )
        case PipelineReportingType.console:
            return PipelineConsoleReportingConfig()
        case _:
            # relative to the root_dir
            return PipelineFileReportingConfig(base_dir=settings.reporting.base_dir)


def _get_storage_config(
    settings: DefaultConfigParametersDict,
) -> PipelineStorageConfigTypes:
    """Get the storage type from the settings."""
    root_dir = settings.root_dir
    match settings.storage.type:
        case PipelineStorageType.memory:
            return PipelineMemoryStorageConfig()
        case PipelineStorageType.file:
            # relative to the root_dir
            return PipelineFileStorageConfig(
                base_dir=str(Path(root_dir) / settings.storage.base_dir)
            )
        case PipelineStorageType.blob:
            return PipelineBlobStorageConfig(
                connection_string=settings.storage.connection_string,
                container_name=settings.storage.container_name,
                base_dir=settings.storage.base_dir,
            )
        case _:
            # relative to the root_dir
            return PipelineFileStorageConfig(
                base_dir=str(Path(root_dir) / settings.storage.base_dir)
            )


def _get_cache_config(
    settings: DefaultConfigParametersDict,
) -> PipelineCacheConfigTypes:
    """Get the cache type from the settings."""
    match settings.cache.type:
        case PipelineCacheType.memory:
            return PipelineMemoryCacheConfig()
        case PipelineCacheType.file:
            # relative to root dir
            return PipelineFileCacheConfig(base_dir=settings.cache.base_dir)
        case PipelineCacheType.none:
            return PipelineNoneCacheConfig()
        case PipelineCacheType.blob:
            return PipelineBlobCacheConfig(
                connection_string=settings.cache.connection_string,
                container_name=settings.cache.container_name,
                base_dir=settings.cache.base_dir,
            )
        case _:
            # relative to root dir
            return PipelineFileCacheConfig(base_dir="./cache")
