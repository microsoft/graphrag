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
    relationship_description_embedding,
    text_unit_text_embedding,
)
from graphrag.config.get_embedding_settings import get_embedding_settings
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.operations.embed_text.embed_text import embed_text
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput
from graphrag.utils.storage import (
    load_table_from_storage,
    write_table_to_storage,
)

logger = logging.getLogger(__name__)


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """All the steps to transform community reports."""
    logger.info("Workflow started: generate_text_embeddings")
    embedded_fields = config.embed_text.names
    logger.info("Embedding the following fields: %s", embedded_fields)
    documents = None
    relationships = None
    text_units = None
    entities = None
    community_reports = None
    if document_text_embedding in embedded_fields:
        documents = await load_table_from_storage("documents", context.output_storage)
    if relationship_description_embedding in embedded_fields:
        relationships = await load_table_from_storage(
            "relationships", context.output_storage
        )
    if text_unit_text_embedding in embedded_fields:
        text_units = await load_table_from_storage("text_units", context.output_storage)
    if (
        entity_title_embedding in embedded_fields
        or entity_description_embedding in embedded_fields
    ):
        entities = await load_table_from_storage("entities", context.output_storage)
    if (
        community_title_embedding in embedded_fields
        or community_summary_embedding in embedded_fields
        or community_full_content_embedding in embedded_fields
    ):
        community_reports = await load_table_from_storage(
            "community_reports", context.output_storage
        )

    text_embed = get_embedding_settings(config)

    output = await generate_text_embeddings(
        documents=documents,
        relationships=relationships,
        text_units=text_units,
        entities=entities,
        community_reports=community_reports,
        callbacks=context.callbacks,
        cache=context.cache,
        text_embed_config=text_embed,
        embedded_fields=embedded_fields,
    )

    if config.snapshots.embeddings:
        for name, table in output.items():
            await write_table_to_storage(
                table,
                f"embeddings.{name}",
                context.output_storage,
            )

    logger.info("Workflow completed: generate_text_embeddings")
    return WorkflowFunctionOutput(result=output)


async def generate_text_embeddings(
    documents: pd.DataFrame | None,
    relationships: pd.DataFrame | None,
    text_units: pd.DataFrame | None,
    entities: pd.DataFrame | None,
    community_reports: pd.DataFrame | None,
    callbacks: WorkflowCallbacks,
    cache: PipelineCache,
    text_embed_config: dict,
    embedded_fields: list[str],
) -> dict[str, pd.DataFrame]:
    """All the steps to generate all embeddings."""
    embedding_param_map = {
        document_text_embedding: {
            "data": documents.loc[:, ["id", "text"]] if documents is not None else None,
            "embed_column": "text",
        },
        relationship_description_embedding: {
            "data": relationships.loc[:, ["id", "description"]]
            if relationships is not None
            else None,
            "embed_column": "description",
        },
        text_unit_text_embedding: {
            "data": text_units.loc[:, ["id", "text"]]
            if text_units is not None
            else None,
            "embed_column": "text",
        },
        entity_title_embedding: {
            "data": entities.loc[:, ["id", "title"]] if entities is not None else None,
            "embed_column": "title",
        },
        entity_description_embedding: {
            "data": entities.loc[:, ["id", "title", "description"]].assign(
                title_description=lambda df: df["title"] + ":" + df["description"]
            )
            if entities is not None
            else None,
            "embed_column": "title_description",
        },
        community_title_embedding: {
            "data": community_reports.loc[:, ["id", "title"]]
            if community_reports is not None
            else None,
            "embed_column": "title",
        },
        community_summary_embedding: {
            "data": community_reports.loc[:, ["id", "summary"]]
            if community_reports is not None
            else None,
            "embed_column": "summary",
        },
        community_full_content_embedding: {
            "data": community_reports.loc[:, ["id", "full_content"]]
            if community_reports is not None
            else None,
            "embed_column": "full_content",
        },
    }

    logger.info("Creating embeddings")
    outputs = {}
    for field in embedded_fields:
        if embedding_param_map[field]["data"] is None:
            msg = f"Embedding {field} is specified but data table is not in storage. This may or may not be intentional - if you expect it to me here, please check for errors earlier in the logs."
            logger.warning(msg)
        else:
            outputs[field] = await _run_embeddings(
                name=field,
                callbacks=callbacks,
                cache=cache,
                text_embed_config=text_embed_config,
                **embedding_param_map[field],
            )
    return outputs


async def _run_embeddings(
    name: str,
    data: pd.DataFrame,
    embed_column: str,
    callbacks: WorkflowCallbacks,
    cache: PipelineCache,
    text_embed_config: dict,
) -> pd.DataFrame:
    """All the steps to generate single embedding."""
    data["embedding"] = await embed_text(
        input=data,
        callbacks=callbacks,
        cache=cache,
        embed_column=embed_column,
        embedding_name=name,
        strategy=text_embed_config["strategy"],
    )

    return data.loc[:, ["id", "embedding"]]
