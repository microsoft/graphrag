# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging

import pandas as pd

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
from graphrag.config.get_vector_store_settings import get_vector_store_settings
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.operations.embed_text.embed_text import embed_text
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput
from graphrag.language_model.manager import ModelManager
from graphrag.language_model.protocol.base import EmbeddingModel
from graphrag.tokenizer.get_tokenizer import get_tokenizer
from graphrag.tokenizer.tokenizer import Tokenizer
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

    vector_store_config = get_vector_store_settings(config)

    model_config = config.get_language_model_config(config.embed_text.model_id)

    model = ModelManager().get_or_create_embedding_model(
        name="text_embedding",
        model_type=model_config.type,
        config=model_config,
        callbacks=context.callbacks,
        cache=context.cache,
    )

    tokenizer = get_tokenizer(model_config)

    output = await generate_text_embeddings(
        documents=documents,
        relationships=relationships,
        text_units=text_units,
        entities=entities,
        community_reports=community_reports,
        callbacks=context.callbacks,
        model=model,
        tokenizer=tokenizer,
        batch_size=config.embed_text.batch_size,
        batch_max_tokens=config.embed_text.batch_max_tokens,
        num_threads=model_config.concurrent_requests,
        vector_store_config=vector_store_config,
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
    model: EmbeddingModel,
    tokenizer: Tokenizer,
    batch_size: int,
    batch_max_tokens: int,
    num_threads: int,
    vector_store_config: dict,
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
                model=model,
                tokenizer=tokenizer,
                vector_store_config=vector_store_config,
                batch_size=batch_size,
                batch_max_tokens=batch_max_tokens,
                num_threads=num_threads,
                **embedding_param_map[field],
            )
    return outputs


async def _run_embeddings(
    name: str,
    data: pd.DataFrame,
    embed_column: str,
    callbacks: WorkflowCallbacks,
    model: EmbeddingModel,
    tokenizer: Tokenizer,
    batch_size: int,
    batch_max_tokens: int,
    num_threads: int,
    vector_store_config: dict,
) -> pd.DataFrame:
    """All the steps to generate single embedding."""
    data["embedding"] = await embed_text(
        input=data,
        callbacks=callbacks,
        model=model,
        tokenizer=tokenizer,
        embed_column=embed_column,
        embedding_name=name,
        batch_size=batch_size,
        batch_max_tokens=batch_max_tokens,
        num_threads=num_threads,
        vector_store_config=vector_store_config,
    )

    return data.loc[:, ["id", "embedding"]]
