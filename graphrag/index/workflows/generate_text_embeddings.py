# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging

import pandas as pd

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.embeddings import (
    community_full_content_embedding,
    community_summary_embedding,
    community_title_embedding,
    document_text_embedding,
    entity_description_embedding,
    entity_title_embedding,
    get_embedded_fields,
    get_embedding_settings,
    relationship_description_embedding,
    text_unit_text_embedding,
)
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.context import PipelineRunContext
from graphrag.index.operations.embed_text import embed_text
from graphrag.index.typing import WorkflowFunctionOutput
from graphrag.storage.pipeline_storage import PipelineStorage
from graphrag.utils.storage import load_table_from_storage, write_table_to_storage

log = logging.getLogger(__name__)


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
    callbacks: WorkflowCallbacks,
) -> WorkflowFunctionOutput:
    """All the steps to transform community reports."""
    final_documents = await load_table_from_storage("documents", context.storage)
    final_relationships = await load_table_from_storage(
        "relationships", context.storage
    )
    final_text_units = await load_table_from_storage("text_units", context.storage)
    final_entities = await load_table_from_storage("entities", context.storage)
    final_community_reports = await load_table_from_storage(
        "community_reports", context.storage
    )

    embedded_fields = get_embedded_fields(config)
    text_embed = get_embedding_settings(config)

    await generate_text_embeddings(
        final_documents=final_documents,
        final_relationships=final_relationships,
        final_text_units=final_text_units,
        final_entities=final_entities,
        final_community_reports=final_community_reports,
        callbacks=callbacks,
        cache=context.cache,
        storage=context.storage,
        text_embed_config=text_embed,
        embedded_fields=embedded_fields,
        snapshot_embeddings_enabled=config.snapshots.embeddings,
    )

    return WorkflowFunctionOutput(result=None, config=None)


async def generate_text_embeddings(
    final_documents: pd.DataFrame | None,
    final_relationships: pd.DataFrame | None,
    final_text_units: pd.DataFrame | None,
    final_entities: pd.DataFrame | None,
    final_community_reports: pd.DataFrame | None,
    callbacks: WorkflowCallbacks,
    cache: PipelineCache,
    storage: PipelineStorage,
    text_embed_config: dict,
    embedded_fields: set[str],
    snapshot_embeddings_enabled: bool = False,
) -> None:
    """All the steps to generate all embeddings."""
    embedding_param_map = {
        document_text_embedding: {
            "data": final_documents.loc[:, ["id", "text"]]
            if final_documents is not None
            else None,
            "embed_column": "text",
        },
        relationship_description_embedding: {
            "data": final_relationships.loc[:, ["id", "description"]]
            if final_relationships is not None
            else None,
            "embed_column": "description",
        },
        text_unit_text_embedding: {
            "data": final_text_units.loc[:, ["id", "text"]]
            if final_text_units is not None
            else None,
            "embed_column": "text",
        },
        entity_title_embedding: {
            "data": final_entities.loc[:, ["id", "title"]]
            if final_entities is not None
            else None,
            "embed_column": "title",
        },
        entity_description_embedding: {
            "data": final_entities.loc[:, ["id", "title", "description"]].assign(
                title_description=lambda df: df["title"] + ":" + df["description"]
            )
            if final_entities is not None
            else None,
            "embed_column": "title_description",
        },
        community_title_embedding: {
            "data": final_community_reports.loc[:, ["id", "title"]]
            if final_community_reports is not None
            else None,
            "embed_column": "title",
        },
        community_summary_embedding: {
            "data": final_community_reports.loc[:, ["id", "summary"]]
            if final_community_reports is not None
            else None,
            "embed_column": "summary",
        },
        community_full_content_embedding: {
            "data": final_community_reports.loc[:, ["id", "full_content"]]
            if final_community_reports is not None
            else None,
            "embed_column": "full_content",
        },
    }

    log.info("Creating embeddings")
    for field in embedded_fields:
        await _run_and_snapshot_embeddings(
            name=field,
            callbacks=callbacks,
            cache=cache,
            storage=storage,
            text_embed_config=text_embed_config,
            snapshot_embeddings_enabled=snapshot_embeddings_enabled,
            **embedding_param_map[field],
        )


async def _run_and_snapshot_embeddings(
    name: str,
    data: pd.DataFrame,
    embed_column: str,
    callbacks: WorkflowCallbacks,
    cache: PipelineCache,
    storage: PipelineStorage,
    text_embed_config: dict,
    snapshot_embeddings_enabled: bool,
) -> None:
    """All the steps to generate single embedding."""
    if text_embed_config:
        data["embedding"] = await embed_text(
            input=data,
            callbacks=callbacks,
            cache=cache,
            embed_column=embed_column,
            embedding_name=name,
            strategy=text_embed_config["strategy"],
        )

        if snapshot_embeddings_enabled is True:
            data = data.loc[:, ["id", "embedding"]]
            await write_table_to_storage(data, f"embeddings.{name}", storage)
